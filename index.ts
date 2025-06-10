import * as dotenv from "dotenv";
import { Telegraf } from "telegraf";
import { message } from "telegraf/filters";
import { createWriteStream, mkdirSync } from "node:fs";
import { Writable } from "node:stream";
import { createPost, getRandomPost } from "$services/postService";
import { AssetType, PostDto } from "$dto";

dotenv.config();
// ensure photos directory exists
mkdirSync("./photos", { recursive: true });

if (process.env.BOT_TOKEN === undefined) {
  throw new TypeError("BOT_TOKEN must be provided!");
}

const bot = new Telegraf(process.env.BOT_TOKEN, {});

// small helper
const download = async (fromFileId: string, toPath: string) => {
  const link = await bot.telegram.getFileLink(fromFileId);
  const res = await fetch(link.toString());
  await res.body!.pipeTo(Writable.toWeb(createWriteStream(toPath)));
};

bot.on("channel_post", async (ctx) => {
  console.log(ctx.senderChat);
});
// handler that downloads all photos the bot sees to a photos
bot.on(message("photo"), async (ctx) => {
  // take the last photosize (highest size)
  const { file_id } = ctx.message.photo.pop()!;
  await createPost({
    assets: [
      {
        assetType: AssetType.IMAGE,
        fileId: file_id,
      },
    ],
    text: "text",
  });
  // const path = `./photos/${file_id}.jpg`;
  const link = await bot.telegram.getFileLink(file_id);

  // await download(file_id, path);
  // console.log("Downloaded", path);
  // await bot.telegram.sendPhoto('-1002326830163', file_id)
});

async function makeNewPost(channelId: string) {
  const post = await getRandomPost();
  if (post != null) {
    await bot.telegram.sendPhoto(channelId, post.text);
  }
}

bot.launch();
