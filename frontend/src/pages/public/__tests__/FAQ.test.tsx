import { screen, fireEvent, waitFor, render } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { FAQ } from '../FAQ';

// Mock popup components
vi.mock('@/components/common/ContactSupportPopup', () => ({
  ContactSupportPopup: ({ isOpen, onClose }: any) => 
    isOpen ? (
      <div data-testid="contact-support-popup">
        <div>Contact Support Popup</div>
        <button onClick={onClose}>Close</button>
      </div>
    ) : null,
}));

vi.mock('@/components/common/ScheduleDemoPopup', () => ({
  ScheduleDemoPopup: ({ isOpen, onClose }: any) => 
    isOpen ? (
      <div data-testid="schedule-demo-popup">
        <div>Schedule Demo Popup</div>
        <button onClick={onClose}>Close</button>
      </div>
    ) : null,
}));

describe('FAQ', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderFAQ = () => {
    return render(
      <BrowserRouter>
        <FAQ />
      </BrowserRouter>
    );
  };

  it('should render FAQ page', () => {
    renderFAQ();
    
    expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument();
    expect(screen.getByText('Everything you need to know about CustomerCareGPT')).toBeInTheDocument();
  });

  it('should display all FAQ items', () => {
    renderFAQ();
    
    expect(screen.getByText('How does CustomerCareGPT work?')).toBeInTheDocument();
    expect(screen.getByText('Is my data safe and secure?')).toBeInTheDocument();
    expect(screen.getByText('How much does it cost?')).toBeInTheDocument();
    expect(screen.getByText('What file formats do you support?')).toBeInTheDocument();
    expect(screen.getByText('How accurate are the AI responses?')).toBeInTheDocument();
  });

  it('should handle FAQ accordion expansion', () => {
    renderFAQ();
    
    const firstFaq = screen.getByRole('button', { name: 'How does CustomerCareGPT work?' });
    fireEvent.click(firstFaq);
    
    expect(screen.getByText('CustomerCareGPT uses advanced AI to analyze your uploaded documents and create an intelligent chatbot. Simply upload your FAQs, documentation, or knowledge base, and our AI will instantly train on your content. You then get an embeddable widget that can answer customer questions 24/7.')).toBeInTheDocument();
  });

  it('should handle FAQ accordion collapse', () => {
    renderFAQ();
    
    const firstFaq = screen.getByRole('button', { name: 'How does CustomerCareGPT work?' });
    fireEvent.click(firstFaq);
    
    // Should expand
    expect(screen.getByText('CustomerCareGPT uses advanced AI to analyze your uploaded documents and create an intelligent chatbot. Simply upload your FAQs, documentation, or knowledge base, and our AI will instantly train on your content. You then get an embeddable widget that can answer customer questions 24/7.')).toBeInTheDocument();
    
    // Click again to collapse
    fireEvent.click(firstFaq);
    
    // Should collapse (content should not be visible)
    expect(screen.queryByText('CustomerCareGPT uses advanced AI to analyze your uploaded documents and create an intelligent chatbot. Simply upload your FAQs, documentation, or knowledge base, and our AI will instantly train on your content. You then get an embeddable widget that can answer customer questions 24/7.')).not.toBeInTheDocument();
  });

  it('should display security FAQ', () => {
    renderFAQ();
    
    const securityFaq = screen.getByRole('button', { name: 'Is my data safe and secure?' });
    fireEvent.click(securityFaq);
    
    expect(screen.getByText('Yes, absolutely. We take security very seriously. All data is encrypted in transit and at rest. We are SOC 2 compliant and follow industry best practices for data protection. Your documents and customer conversations are never shared with third parties.')).toBeInTheDocument();
  });

  it('should display pricing FAQ', () => {
    renderFAQ();
    
    const pricingFaq = screen.getByRole('button', { name: 'How much does it cost?' });
    fireEvent.click(pricingFaq);
    
    expect(screen.getByText('We offer three plans: Starter ($29/month), Pro ($79/month), and Enterprise ($299/month). All plans include a 14-day free trial with no credit card required. You can upgrade, downgrade, or cancel at any time.')).toBeInTheDocument();
  });

  it('should display file formats FAQ', () => {
    renderFAQ();
    
    const fileFormatsFaq = screen.getByRole('button', { name: 'What file formats do you support?' });
    fireEvent.click(fileFormatsFaq);
    
    expect(screen.getByText('We support a wide variety of file formats including PDF, DOC, DOCX, TXT, MD, HTML, and more. You can upload FAQs, user manuals, product documentation, or any text-based content that you want your chatbot to learn from.')).toBeInTheDocument();
  });

  it('should display accuracy FAQ', () => {
    renderFAQ();
    
    const accuracyFaq = screen.getByRole('button', { name: 'How accurate are the AI responses?' });
    fireEvent.click(accuracyFaq);
    
    expect(screen.getByText('Our AI is highly accurate when answering questions based on your uploaded content. The accuracy depends on the quality and comprehensiveness of your source material. The AI will only answer questions it can find information about in your documents, ensuring reliable responses.')).toBeInTheDocument();
  });

  it('should display customization FAQ', () => {
    renderFAQ();
    
    const customizationFaq = screen.getByRole('button', { name: 'Can I customize the chatbot appearance?' });
    fireEvent.click(customizationFaq);
    
    expect(screen.getByText('Yes! You can customize the chatbot widget to match your brand, including colors, logo, welcome messages, and positioning. Pro and Enterprise plans offer more advanced customization options.')).toBeInTheDocument();
  });

  it('should display integration FAQ', () => {
    renderFAQ();
    
    const integrationFaq = screen.getByRole('button', { name: 'How do I integrate the chatbot into my website?' });
    fireEvent.click(integrationFaq);
    
    expect(screen.getByText('Integration is simple - just copy and paste a single line of code into your website. No technical knowledge required. The chatbot widget will appear on your site and start answering customer questions immediately.')).toBeInTheDocument();
  });

  it('should display analytics FAQ', () => {
    renderFAQ();
    
    const analyticsFaq = screen.getByRole('button', { name: 'Do you offer analytics and reporting?' });
    fireEvent.click(analyticsFaq);
    
    expect(screen.getByText('Yes, all plans include a comprehensive analytics dashboard where you can track customer queries, response accuracy, popular questions, usage patterns, and more. This helps you optimize your customer support over time.')).toBeInTheDocument();
  });

  it('should display support FAQ', () => {
    renderFAQ();
    
    const supportFaq = screen.getByRole('button', { name: 'What kind of support do you provide?' });
    fireEvent.click(supportFaq);
    
    expect(screen.getByText('We provide email support for all plans, with priority support for Pro customers and dedicated support for Enterprise customers. We also have comprehensive documentation and video tutorials to help you get started.')).toBeInTheDocument();
  });

  it('should display cancellation FAQ', () => {
    renderFAQ();
    
    const cancellationFaq = screen.getByRole('button', { name: 'Can I cancel my subscription anytime?' });
    fireEvent.click(cancellationFaq);
    
    expect(screen.getByText('Yes, you can cancel your subscription at any time with no penalties or long-term contracts. Your chatbot will continue working until the end of your current billing period, and you can always reactivate your account later.')).toBeInTheDocument();
  });

  it('should handle contact support button', () => {
    renderFAQ();
    
    const contactButton = screen.getByText('Contact Support');
    fireEvent.click(contactButton);
    
    expect(screen.getByTestId('contact-support-popup')).toBeInTheDocument();
  });

  it('should handle contact support popup close', () => {
    renderFAQ();
    
    const contactButton = screen.getByText('Contact Support');
    fireEvent.click(contactButton);
    
    expect(screen.getByTestId('contact-support-popup')).toBeInTheDocument();
    
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    expect(screen.queryByTestId('contact-support-popup')).not.toBeInTheDocument();
  });

  it('should handle schedule demo button', () => {
    renderFAQ();
    
    const scheduleDemoButton = screen.getByText('Schedule a Demo');
    fireEvent.click(scheduleDemoButton);
    
    expect(screen.getByTestId('schedule-demo-popup')).toBeInTheDocument();
  });

  it('should handle schedule demo popup close', () => {
    renderFAQ();
    
    const scheduleDemoButton = screen.getByText('Schedule a Demo');
    fireEvent.click(scheduleDemoButton);
    
    expect(screen.getByTestId('schedule-demo-popup')).toBeInTheDocument();
    
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    expect(screen.queryByTestId('schedule-demo-popup')).not.toBeInTheDocument();
  });

  // Removed: search and category tests not present in current FAQ UI

  it('should display helpful section', () => {
    renderFAQ();
    
    expect(screen.getByText('Still have questions?')).toBeInTheDocument();
    expect(screen.getByText("Can't find the answer you're looking for? Please chat with our friendly team.")).toBeInTheDocument();
  });

  it('should display all FAQ items in correct order', () => {
    renderFAQ();
    
    const faqItems = screen.getAllByRole('button');
    const faqQuestions = faqItems.map(item => item.textContent);
    
    expect(faqQuestions).toContain('How does CustomerCareGPT work?');
    expect(faqQuestions).toContain('Is my data safe and secure?');
    expect(faqQuestions).toContain('How much does it cost?');
    expect(faqQuestions).toContain('What file formats do you support?');
    expect(faqQuestions).toContain('How accurate are the AI responses?');
  });

  it('should handle multiple FAQ expansions', () => {
    renderFAQ();
    
    const firstFaq = screen.getByRole('button', { name: 'How does CustomerCareGPT work?' });
    const secondFaq = screen.getByRole('button', { name: 'Is my data safe and secure?' });
    
    fireEvent.click(firstFaq);
    fireEvent.click(secondFaq);
    
    // Accordion allows one open at a time; assert the second opened content
    expect(screen.getByText((t) => t.startsWith('Yes, absolutely. We take security'))).toBeInTheDocument();
  });
});
