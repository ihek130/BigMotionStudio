import Header from '@/components/layout/Header'
import Footer from '@/components/layout/Footer'

export default function PrivacyPolicy() {
  return (
    <main className="min-h-screen bg-white">
      <Header />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Privacy Policy</h1>
        <p className="text-sm text-gray-600 mb-8">Last updated: {new Date().toLocaleDateString()}</p>

        <div className="prose prose-lg max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Introduction</h2>
            <p className="text-gray-700 mb-4">
              Welcome to Big Motion Studio. We respect your privacy and are committed to protecting your personal data. 
              This privacy policy will inform you about how we handle your personal data when you visit our website and 
              use our services.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Information We Collect</h2>
            <p className="text-gray-700 mb-4">We collect and process the following types of information:</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2 mb-4">
              <li><strong>Account Information:</strong> Email address, name, and password when you create an account</li>
              <li><strong>Platform Connections:</strong> OAuth tokens for YouTube, TikTok, and Instagram when you connect these platforms</li>
              <li><strong>Content Data:</strong> Video series settings, generated content, and scheduling preferences</li>
              <li><strong>Usage Data:</strong> How you interact with our service, including pages visited and features used</li>
              <li><strong>Payment Information:</strong> Billing details processed securely through our payment provider</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">How We Use Your Information</h2>
            <p className="text-gray-700 mb-4">We use your information to:</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2 mb-4">
              <li>Provide and maintain our video generation and posting services</li>
              <li>Process your video creation requests and schedule posts to connected platforms</li>
              <li>Communicate with you about your account and service updates</li>
              <li>Improve our services and develop new features</li>
              <li>Ensure the security and integrity of our platform</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Data Storage and Security</h2>
            <p className="text-gray-700 mb-4">
              We implement industry-standard security measures to protect your data. Your platform OAuth tokens are 
              encrypted, and we use secure connections (HTTPS) for all data transmission. Generated videos are 
              automatically deleted after successful upload to your platforms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Third-Party Services</h2>
            <p className="text-gray-700 mb-4">
              We integrate with the following third-party services to provide our functionality:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2 mb-4">
              <li><strong>YouTube, TikTok, Instagram:</strong> For posting videos to your accounts (with your authorization)</li>
              <li><strong>OpenAI:</strong> For AI-powered script generation</li>
              <li><strong>DeepInfra:</strong> For AI image generation</li>
              <li><strong>Audixa:</strong> For text-to-speech voice generation</li>
              <li><strong>Payment Processors:</strong> For handling subscription payments</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Your Rights</h2>
            <p className="text-gray-700 mb-4">You have the right to:</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2 mb-4">
              <li>Access your personal data</li>
              <li>Correct inaccurate data</li>
              <li>Request deletion of your data</li>
              <li>Export your data</li>
              <li>Withdraw consent for platform connections</li>
              <li>Object to processing of your data</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Data Retention</h2>
            <p className="text-gray-700 mb-4">
              We retain your account data as long as your account is active. If you delete your account, we will 
              remove your personal data within 30 days, except where we are required to retain it for legal purposes.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Contact Us</h2>
            <p className="text-gray-700 mb-4">
              If you have any questions about this Privacy Policy or our data practices, please contact us at:
            </p>
            <p className="text-gray-700">
              <strong>Email:</strong> <a href="mailto:support@bigmotionstudio.com" className="text-emerald-600 hover:text-emerald-700">support@bigmotionstudio.com</a>
            </p>
          </section>
        </div>
      </div>
      <Footer />
    </main>
  )
}
