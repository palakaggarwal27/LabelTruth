export function buildProductLink(productName: string, storeUrl?: string): string {
  const baseUrl = storeUrl || `https://www.blinkit.com/s/?q=${encodeURIComponent(productName)}`;
  const affiliateTag = "labeltruth-21"; 
  return `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}tag=${affiliateTag}`;
}
