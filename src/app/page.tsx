import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import Ticker from "@/components/Ticker";
import HowItWorks from "@/components/HowItWorks";
import Services from "@/components/Services";
import WhyCarTrust from "@/components/WhyCarTrust";
import SampleReports from "@/components/SampleReports";
import FAQ from "@/components/FAQ";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <Ticker />
        <HowItWorks />
        <Services />
        <WhyCarTrust />
        <SampleReports />
        <FAQ />
      </main>
      <Footer />
    </>
  );
}
