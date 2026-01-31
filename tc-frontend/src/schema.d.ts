export interface ItemMeta {
    id: number
    title: string
    description: string
    update_time: Date
    tags: Tag[]
}

export interface Tag {
    id: number
    name: string
}