export interface ProductSummary {
  product_id: string
  name: string
  garment_type: string
  description: string
  price: number
  image_url: string
  colors: string[]
  total_stock: number
}

export interface SizeStock {
  size: string
  quantity: number
}

export interface ProductDetail extends ProductSummary {
  colors: string[]
  search_tags: string[]
  sizes: SizeStock[]
  total_stock: number
}

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
}

// What the chat endpoint returns for a matched product — a ProductSummary
// enriched with live stock, but without the full catalogue detail fields.
export interface ChatProduct extends ProductSummary {
  sizes: SizeStock[]
  total_stock: number
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
  product_ids?: string[]
}
