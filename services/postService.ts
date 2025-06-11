import { PrismaClient } from "@prisma/client";
import { PostDto } from "$dto";
import prismaRandom from "prisma-extension-random";

const client = new PrismaClient().$extends(prismaRandom());

export async function createPost(post: PostDto) {
  return client.post.create({
    data: {
      text: post.text,
      assets: {
        create: post.assets.map((a) => ({ fileId: a.fileId })),
      },
    },
  });
}

export async function getRandomPost() {
  return await client.post.findRandom({});
}

export async function deletePost(id: number) {
  return client.post.delete({
    where: {
      id,
    },
  });
}

export async function registerNewSourceWithTarget(
  sourceId: number,
  targetId: number,
) {
  return client.sourceChat.create({
    data: {
      chatId: sourceId,
      targets: {
        create: {
          channelId: targetId,
        },
      },
    },
  });
}
