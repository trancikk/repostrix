export interface PostDto {
    assets: AssetDto[]
    text: string
}

export interface AssetDto {
    assetType: AssetType,
    fileId: string
}

export enum AssetType {
    IMAGE,
    VIDEO,
}