export type { TagMeta } from "@mizip/metahub"

export interface ItemMeta {
    id: string | null
    title: string
    description: string
    update_time: Date
    tags: TagMeta[]
    data_type: string = null
}

export interface ItemDetail extends ItemMeta{

}