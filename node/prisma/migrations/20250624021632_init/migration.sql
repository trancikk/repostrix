-- CreateTable
CREATE TABLE "Post" (
    "id" SERIAL NOT NULL,
    "text" TEXT NOT NULL,

    CONSTRAINT "Post_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Asset" (
    "id" SERIAL NOT NULL,
    "fileId" TEXT NOT NULL,
    "postId" INTEGER NOT NULL,

    CONSTRAINT "Asset_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SourceChat" (
    "id" SERIAL NOT NULL,
    "chatId" BIGINT NOT NULL,

    CONSTRAINT "SourceChat_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TargetChannel" (
    "id" SERIAL NOT NULL,
    "channelId" BIGINT NOT NULL,
    "sourceChatId" INTEGER NOT NULL,

    CONSTRAINT "TargetChannel_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "Asset" ADD CONSTRAINT "Asset_postId_fkey" FOREIGN KEY ("postId") REFERENCES "Post"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TargetChannel" ADD CONSTRAINT "TargetChannel_sourceChatId_fkey" FOREIGN KEY ("sourceChatId") REFERENCES "SourceChat"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
