import logging
import re
from datetime import time, datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatType as ChatTypeTelegram
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, BotCommand
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import IntervalType, ChatStatus, ChatType
from db.repo import find_channel_by_username_or_id, add_channel_mapping, update_channel_schedule_preferences, \
    find_channel_by_id, add_new_channel_or_group
from utils import resolve_timezone

channel_router = Router(name='channel')

EVERY_DAY = 'every_day'
TWICE_PER_DAY = 'twice_per_day'
EVERY_TWO_DAYS = 'every_2_days'

schedule_selection = {
    "Immediately": 0,
    "Each minute": 1 / 60,
    "Each 5 min": 1 / 12,
    "Each 30 min": 1 / 2,
    "Each Hour": 1,
    'Each 2 Hours': 2,
    'Each 6 Hours': 6,
    "Twice per Day": TWICE_PER_DAY,
    "Every Day": EVERY_DAY,
    "Every 2 Days": EVERY_TWO_DAYS,
}

channel_commands = [
    BotCommand(command="schedule_settings", description="Register new channel"),
    BotCommand(command="register_me", description="Register this group"),
    BotCommand(command="enable", description="Enable posts saving and reposting"),
    BotCommand(command="disable", description="Disable posts saving and reposting"),
]


def get_scheduling_kb():
    builder = InlineKeyboardBuilder()
    for i, v in schedule_selection.items():
        value = round(v, 4) if isinstance(v, float) else v
        builder.button(text=i, callback_data=f"schedule_selection:{value}")
    builder.adjust(3)
    return builder.as_markup()


scheduling_kb = get_scheduling_kb()


class ChannelRegistrationForm(StatesGroup):
    name_input = State()
    interval_input = State()
    time_input = State()
    timezone_input = State()


async def _register_channel(message: Message, channel_name_or_id: str | int, session: AsyncSession, state: FSMContext):
    existing_channel = await find_channel_by_username_or_id(session, channel_name_or_id)
    if existing_channel is not None:
        # TODO check if the user is admin
        await add_channel_mapping(session, message.chat.id, existing_channel.id)
        await state.update_data(channel_id=existing_channel.id)
        await state.set_state(ChannelRegistrationForm.interval_input)
        await message.reply(
            f"Channel {channel_name_or_id} has been mapped to this chat. You can send your posts here")
        return await message.answer("How often do you want posts to be sent?", reply_markup=scheduling_kb)
    else:
        return await message.reply("Please add Bot to admins first to the target channel.")


@channel_router.message(Command('register_me'))
async def register_new_channel_via_command(message: Message, session: AsyncSession, state: FSMContext):
    existing_group = await find_channel_by_id(session, message.chat.id)
    if existing_group is not None:
        await message.reply(
            "This group has been already registered. If you want to register a chat, follow /register command")
    else:
        chat_type = ChatType.GROUP if message.chat.type == ChatTypeTelegram.GROUP else ChatType.PRIVATE
        new_chat = await add_new_channel_or_group(session, chat_id=message.chat.id, username=message.chat.username,
                                                  channel_name=message.chat.title, channel_type=chat_type)
        logging.info("Registered new source chat.id: %s, title: %s, username: %s", new_chat.id, new_chat.name,
                     new_chat.username)
        await message.reply(
            f"New channel has been added to this group. You can send your posts here")


@channel_router.message(Command('register'))
async def register_new_channel_via_command(message: Message, session: AsyncSession, state: FSMContext):
    args = message.text.split(' ')
    if len(args) < 2:
        await state.set_state(ChannelRegistrationForm.name_input)
        return await message.answer("Please provide channel name or ID")
    else:
        channel_name_or_id = args[1].strip().replace('@', '').lower()
        return await _register_channel(message, channel_name_or_id, session, state)


@channel_router.message(ChannelRegistrationForm.name_input)
async def register_new_channel_via_state(message: Message, session: AsyncSession, state: FSMContext):
    channel_name = message.text.strip().replace('@', '').lower()
    return await _register_channel(message, channel_name, session, state)


async def update_channel_schedule_pref(session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get('channel_id')
    interval = data.get('interval')
    interval_unit = data.get('interval_unit')
    timezone = data.get('timezone')
    times = data.get('times')
    await state.clear()
    logging.info(f"Updating channel schedule pref: each {interval} {interval_unit} in {timezone}, times: {times}")
    await update_channel_schedule_preferences(session=session, channel_id=channel_id, interval_value=interval,
                                              interval_unit=interval_unit, timezone=timezone, selected_times=times)


@channel_router.message(Command(commands=['disable']))
async def disable_saving_handler(message: Message, session: AsyncSession):
    channel = await find_channel_by_id(session, channel_id=message.chat.id)
    if channel is not None:
        channel.status = ChatStatus.DISABLED
        return await message.reply("Posts saving has been disabled. To enable, type in /enable")
    return await message.answer("Something went wrong.")


@channel_router.message(Command(commands=['enable']))
async def enable_saving_handler(message: Message, session: AsyncSession):
    channel = await find_channel_by_id(session, channel_id=message.chat.id)
    if channel is not None:
        channel.status = ChatStatus.ENABLED
        return await message.reply("Posts saving has been enabled. To disable, type in /disable")
    return await message.answer("Something went wrong.")


@channel_router.message(Command(commands=['schedule_settings']))
async def register_new_channel_via_command(message: Message, state: FSMContext):
    await state.update_data(channel_id=message.chat.id)
    await state.set_state(ChannelRegistrationForm.interval_input)
    return await message.answer("Sure, lets change schedule preferences. How often do you want posts to be sent?",
                                reply_markup=scheduling_kb)


@channel_router.callback_query(ChannelRegistrationForm.interval_input)
@channel_router.callback_query(F.data.startswith('schedule_selection'))
async def handle_interval_input(callback_data: CallbackQuery, session: AsyncSession, state: FSMContext):
    data = callback_data.data.split(':')[-1]
    if data is not None:
        match data:
            case x if x in (EVERY_DAY, TWICE_PER_DAY, EVERY_TWO_DAYS):
                interval = 1 if x in (EVERY_DAY, TWICE_PER_DAY) else 2
                await state.update_data(interval=interval, interval_unit=IntervalType.DAY, )
                await state.set_state(ChannelRegistrationForm.time_input)
                return await callback_data.message.answer(
                    "Please provide times you want your posts to be scheduled in format HH24:MM, HH24:MM, ...")
            case y:
                await state.update_data(interval=float(y), interval_unit=IntervalType.HOUR, timezone=ZoneInfo('UTC'))
                await update_channel_schedule_pref(session, state)
                await callback_data.message.answer("Thank you, your schedule preferences has been saved!")
    return None


@channel_router.message(ChannelRegistrationForm.time_input)
async def handle_schedule_time_input(message: Message, state: FSMContext):
    try:
        # TODO handle cases when user selects once or twice per day and provides few times
        provided_times = re.split(r"[,\s]+", message.text.strip())
        provided_parsed_times: list[time] = [datetime.strptime(txt, "%H:%M").time() for txt in provided_times]
        if provided_parsed_times is None or len(provided_times) == 0:
            return await message.answer(
                "Please provide a valid times (coma or space separated) in format HH:MM, HH:MM, ...")
        await state.update_data(times=provided_parsed_times)
        await state.set_state(ChannelRegistrationForm.timezone_input)
        return await message.answer("Please provide desired timezone (default: UTC)")
    except ValueError | TypeError as e:
        logging.error(e)
        return await message.answer("Please provide a valid time")


@channel_router.message(ChannelRegistrationForm.timezone_input)
async def handle_schedule_tz(message: Message, session: AsyncSession, state: FSMContext):
    tz = resolve_timezone(message.text)
    if tz is None:
        return await message.answer("Please provide a valid timezone (like PST and so on)")
    else:
        await state.update_data(timezone=tz)
        await update_channel_schedule_pref(session, state)
        return await message.answer("Your schedule preferences has been saved!")
