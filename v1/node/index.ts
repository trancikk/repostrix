import * as dotenv from "dotenv";
import { Context, Telegraf } from "telegraf";
import { anyOf, message } from "telegraf/filters";
import { createWriteStream } from "node:fs";
import { Writable } from "node:stream";
import {
  createPost,
  getRandomPost,
  getTargetChannelsBySource,
  registerNewSourceWithTarget,
} from "$services/postService";
import { AssetDto, AssetType, PostDto } from "$dto";
import { parseNumber } from "./utils";
import { Asset } from "@prisma/client";

dotenv.config();

const myUser = 499517011;
// ensure photos directory exists
// mkdirSync("./photos", { recursive: true });

if (process.env.BOT_TOKEN === undefined) {
  throw new TypeError("BOT_TOKEN must be provided!");
}

const bot = new Telegraf(process.env.BOT_TOKEN, {});

bot.use(async (ctx, next) => {
  console.log(
    `Message from: ${ctx.message?.from?.id} - ${ctx.message?.from?.first_name}, chat_id: ${ctx?.message?.chat?.id}`,
  );
  if (ctx.message?.from?.id === myUser) {
    await next();
  }
});

bot.command("register", async (ctx) => {
  console.log(`Registering source: ${ctx.chat.id}, target: ${ctx.payload}`);
  const parsedNum = parseNumber(ctx.payload);
  if (parsedNum != null) {
    await registerNewSourceWithTarget(ctx.chat.id, parsedNum);
  }
});

// bot.use(async (ctx, next) => {
//   await next();
// });
// small helper
const download = async (fromFileId: string, toPath: string) => {
  const link = await bot.telegram.getFileLink(fromFileId);
  const res = await fetch(link.toString());
  await res.body!.pipeTo(Writable.toWeb(createWriteStream(toPath)));
};

bot.on(
  anyOf(
    message("text"),
    message("photo"),
    message("video"),
    message("animation"),
  ),
  async (ctx) => {
    const assets: AssetDto[] = [];
    const post: PostDto = {
      assets,
    };
    console.dir(ctx);
    if ("photo" in ctx.message) {
      const { file_id } = ctx.message.photo.pop()!;
      assets.push({
        assetType: AssetType.IMAGE,
        fileId: file_id,
      });
    }
    if ("video" in ctx.message) {
      assets.push({
        fileId: ctx.message.video.file_id,
        assetType: AssetType.VIDEO,
      });
    }
    if ("animation" in ctx.message) {
      assets.push({
        fileId: ctx.message.animation.file_id,
        assetType: AssetType.ANIMATION,
      });
    }
    if ("text" in ctx.message) {
      post.text = ctx.message.text;
    }
    if ("caption" in ctx.message) {
      post.text = ctx.message.caption;
    }
    // await createPost(post);
    const targets = await getTargetChannelsBySource(ctx.message.chat.id);
    if (targets != null) {
      for (const target of targets) {
        await makeNewPostFromPostDto(target.channelId.toString(), post, bot);
      }
    }
  },
);

// bot.on("channel_post", async (ctx) => {
//   console.log(ctx.senderChat);
// });

// bot.on(message("photo", "media_group_id"), ctx => {
//   // These properties are accessible:
//   ctx.message.photo;
//   ctx.message.media_group_id;

// bot.on(message("video"), async (ctx) => {
//   console.dir(ctx);
// });
//
// bot.on(message("animation"), async (ctx) => {
//   console.dir(ctx);
// });
//
// bot.on(message("text"), async (ctx) => {
//   console.dir(ctx.message.text);
// });

// handler that downloads all photos the bot sees to a photos
// bot.on(message("photo"), async (ctx) => {
// take the last photosize (highest size)
// console.dir(ctx.message.photo);
// console.dir(ctx)
// const { file_id } = ctx.message.photo.pop()!;
// await createPost({
//   assets: [
//     {
//       assetType: AssetType.IMAGE,
//       fileId: file_id,
//     },
//   ],
//   text: "text",
// });
// const path = `./photos/${file_id}.jpg`;
// const link = await bot.telegram.getFileLink(file_id);

// await download(file_id, path);
// console.log("Downloaded", path);
// await bot.telegram.sendPhoto('-1002326830163', file_id)
// });

async function makeNewPost(channelId: string) {
  const post = await getRandomPost();
  if (post != null) {
    await bot.telegram.sendPhoto(channelId, post.text);
  }
}

async function makeNewPostFromPostDto(
  channelId: string,
  postDto: PostDto,
  bot: Telegraf<Context>,
) {
  await bot.telegram.sendMessage(channelId, postDto.text ?? "");
}

bot.launch();

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
