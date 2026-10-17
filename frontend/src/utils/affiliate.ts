export interface StoreLinkOption {
  name: string;
  url: string;
  badge?: string;
}

export function buildStoreOptions(productName: string, userLocation?: string): StoreLinkOption[] {
  const locSuffix = userLocation && userLocation.trim() ? ` ${userLocation.trim()}` : '';
  const q = encodeURIComponent(`${productName}${locSuffix}`);
  const affiliateTag = "labeltruth-21";

  return [
    {
      name: 'Blinkit',
      url: `https://www.blinkit.com/s/?q=${q}&tag=${affiliateTag}`,
      badge: '10-15 Min'
    },
    {
      name: 'Zepto',
      url: `https://www.zeptonow.com/search?q=${q}&tag=${affiliateTag}`,
      badge: '10 Min'
    },
    {
      name: 'Instamart',
      url: `https://www.swiggy.com/instamart/search?custom_back=true&query=${q}`,
      badge: 'Quick Delivery'
    },
    {
      name: 'Amazon Fresh',
      url: `https://www.amazon.in/s?k=${q}&i=nowstore&tag=${affiliateTag}`,
      badge: 'Pan-India'
    }
  ];
}

export function buildProductLink(productName: string, storeUrl?: string): string {
  const baseUrl = storeUrl || `https://www.blinkit.com/s/?q=${encodeURIComponent(productName)}`;
  const affiliateTag = "labeltruth-21"; 
  return `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}tag=${affiliateTag}`;
}
