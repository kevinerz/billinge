import { apiClient } from './client'

export function makeCrudApi<T, TWrite = Partial<T>>(basePath: string) {
  return {
    list: async (): Promise<T[]> => (await apiClient.get(`${basePath}/`)).data,
    retrieve: async (id: number): Promise<T> => (await apiClient.get(`${basePath}/${id}/`)).data,
    create: async (values: TWrite): Promise<T> => (await apiClient.post(`${basePath}/`, values)).data,
    update: async (id: number, values: Partial<TWrite>): Promise<T> =>
      (await apiClient.patch(`${basePath}/${id}/`, values)).data,
    remove: async (id: number): Promise<void> => {
      await apiClient.delete(`${basePath}/${id}/`)
    },
  }
}

export function makeReadOnlyApi<T>(basePath: string) {
  return {
    list: async (): Promise<T[]> => (await apiClient.get(`${basePath}/`)).data,
    retrieve: async (id: number): Promise<T> => (await apiClient.get(`${basePath}/${id}/`)).data,
  }
}
