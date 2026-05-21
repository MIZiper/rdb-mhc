export type { TagMeta } from "@mizip/metahub"

export interface ItemMeta {
    id: string | null
    title: string
    description: string
    update_time: Date
    tags: TagMeta[]
    data_type: string | null
    creator_name: string | null
    creator_sub: string | null
    status: string
}

export interface ItemDetail extends ItemMeta{
    content: any
}