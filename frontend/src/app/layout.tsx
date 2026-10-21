import type { Metadata } from 'next';
import './globals.css';
import { HealthProfileProvider } from '@/context/HealthProfileContext';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { HealthProfileModal } from '@/components/HealthProfileModal';

export const metadata: Metadata = {
  title: 'LabelTruth | Transparent Food Labeling & Consumer Protection',
  description: 'Evidence-based food label scanner auditing Indian packaged foods against FSSAI 2020 standards and personalized medical profiles.',
  manifest: '/manifest.json',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="bg-[#FAFAFA] text-zinc-900 antialiased">
      <body className="min-h-screen flex flex-col font-sans">
        <HealthProfileProvider>
          <Navbar />
          <HealthProfileModal />
          <main className="flex-1">{children}</main>
          <Footer />
        </HealthProfileProvider>
      </body>
    </html>
  );
}
