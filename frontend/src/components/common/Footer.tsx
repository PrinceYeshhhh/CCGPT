import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, Twitter, Linkedin, Github } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-gray-900 dark:bg-gray-950 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Bot className="h-8 w-8 text-blue-400" />
              <span className="text-xl font-bold">CustomerCareGPT</span>
            </div>
            <p className="text-gray-400 text-sm">
              AI-powered customer support automation that scales with your business.
            </p>
            <div className="flex space-x-4">
              <Twitter className="h-5 w-5 text-gray-400 hover:text-blue-400 cursor-pointer transition-colors duration-200" />
              <Linkedin className="h-5 w-5 text-gray-400 hover:text-blue-400 cursor-pointer transition-colors duration-200" />
              <Github className="h-5 w-5 text-gray-400 hover:text-blue-400 cursor-pointer transition-colors duration-200" />
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Product</h3>
            <ul className="space-y-2 text-sm">
              <li><Link to="/features" className="text-gray-400 hover:text-white transition-colors duration-200">Features</Link></li>
              <li><Link to="/pricing" className="text-gray-400 hover:text-white transition-colors duration-200">Pricing</Link></li>
              <li><Link to="/faq" className="text-gray-400 hover:text-white transition-colors duration-200">FAQ</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Company</h3>
            <ul className="space-y-2 text-sm">
              <li><Link to="/about" className="text-gray-400 hover:text-white transition-colors duration-200">About</Link></li>
              <li><Link to="/contact" className="text-gray-400 hover:text-white transition-colors duration-200">Contact</Link></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors duration-200">Blog</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Legal</h3>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors duration-200">Privacy Policy</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors duration-200">Terms of Service</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition-colors duration-200">Cookie Policy</a></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 dark:border-gray-700 mt-8 pt-8 text-center text-sm text-gray-400">
          <p>&copy; 2025 CustomerCareGPT. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
