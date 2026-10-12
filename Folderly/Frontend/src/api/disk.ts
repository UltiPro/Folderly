import { http } from './client'
import type { DiskUsage } from '@/types/api'

export async function fetchDiskUsage(): Promise<DiskUsage> {
  const { data } = await http.get<DiskUsage>('/disk')
  return data
}
