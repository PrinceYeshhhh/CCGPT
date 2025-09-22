import React from 'react'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Button } from '@/components/ui/button'

export function FAQ() {
  const faqs = [
    { question: 'How does CustomerCareGPT work?', answer: 'CustomerCareGPT uses advanced AI to analyze your uploaded documents and create an intelligent chatbot. Simply upload your FAQs, documentation, or knowledge base, and our AI will instantly train on your content. You then get an embeddable widget that can answer customer questions 24/7.' },
    { question: 'Is my data safe and secure?', answer: 'Yes, absolutely. We take security very seriously. All data is encrypted in transit and at rest. We are SOC 2 compliant and follow industry best practices for data protection. Your documents and customer conversations are never shared with third parties.' },
    { question: 'How much does it cost?', answer: 'We offer three plans: Starter ($29/month), Pro ($79/month), and Enterprise ($299/month). All plans include a 14-day free trial with no credit card required. You can upgrade, downgrade, or cancel at any time.' },
    { question: 'What file formats do you support?', answer: 'We support a wide variety of file formats including PDF, DOC, DOCX, TXT, MD, HTML, and more. You can upload FAQs, user manuals, product documentation, or any text-based content that you want your chatbot to learn from.' },
    { question: 'How accurate are the AI responses?', answer: 'Our AI is highly accurate when answering questions based on your uploaded content. The accuracy depends on the quality and comprehensiveness of your source material. The AI will only answer questions it can find information about in your documents, ensuring reliable responses.' },
    { question: 'Can I customize the chatbot appearance?', answer: 'Yes! You can customize the chatbot widget to match your brand, including colors, logo, welcome messages, and positioning. Pro and Enterprise plans offer more advanced customization options.' },
    { question: 'How do I integrate the chatbot into my website?', answer: 'Integration is simple - just copy and paste a single line of code into your website. No technical knowledge required. The chatbot widget will appear on your site and start answering customer questions immediately.' },
    { question: 'Do you offer analytics and reporting?', answer: 'Yes, all plans include a comprehensive analytics dashboard where you can track customer queries, response accuracy, popular questions, usage patterns, and more. This helps you optimize your customer support over time.' },
    { question: 'What kind of support do you provide?', answer: 'We provide email support for all plans, with priority support for Pro customers and dedicated support for Enterprise customers. We also have comprehensive documentation and video tutorials to help you get started.' },
    { question: 'Can I cancel my subscription anytime?', answer: 'Yes, you can cancel your subscription at any time with no penalties or long-term contracts. Your chatbot will continue working until the end of your current billing period, and you can always reactivate your account later.' },
  ]

  return (
    <div className="min-h-screen bg-background py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-6">Frequently Asked Questions</h1>
          <p className="text-lg md:text-xl text-muted-foreground">Everything you need to know about CustomerCareGPT</p>
        </div>

        <Accordion className="w-full space-y-4 mb-16">
          {faqs.map((faq, index) => (
            <AccordionItem key={index} value={`item-${index}`} className="border rounded-lg px-6 bg-card">
              <AccordionTrigger className="text-left font-semibold">{faq.question}</AccordionTrigger>
              <AccordionContent className="text-muted-foreground text-base leading-relaxed">{faq.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>

        <div className="text-center bg-muted/50 rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Still have questions?</h2>
          <p className="text-muted-foreground mb-6">Can't find the answer you're looking for? Please chat with our friendly team.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="primary" className="w-full sm:w-auto">Contact Support</Button>
            <Button variant="outline" className="w-full sm:w-auto">Schedule a Demo</Button>
          </div>
        </div>
      </div>
    </div>
  )
}
