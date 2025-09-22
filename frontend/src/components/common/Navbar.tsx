import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { Bot, Menu, X } from 'lucide-react';

interface NavbarProps {
  isAuthenticated?: boolean;
  onLogout?: () => void;
}

export function Navbar({ isAuthenticated = false, onLogout }: NavbarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/features', label: 'Features' },
    { href: '/pricing', label: 'Pricing' },
    { href: '/faq', label: 'FAQ' },
  ];

  return (
    <nav className="bg-background/95 backdrop-blur-md border-b border-border sticky top-0 z-50 transition-all duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <Bot className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-foreground">CustomerCareGPT</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className={`text-sm font-medium transition-colors hover:text-blue-600 ${
                  location.pathname === link.href
                    ? 'text-blue-600'
                    : 'text-muted-foreground'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="hidden md:flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <ThemeToggle />
                <Link to="/dashboard">
                  <Button variant="ghost">Dashboard</Button>
                </Link>
                <Button variant="outline" onClick={onLogout}>
                  Logout
                </Button>
              </>
            ) : (
              <>
                <ThemeToggle />
                <Link to="/login">
                  <Button variant="ghost">Login</Button>
                </Link>
                <Link to="/register">
                  <Button variant="primary">Get Started</Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <ThemeToggle />
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(!isOpen)}
            >
              {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-background border-t border-border animate-fade-in">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  to={link.href}
                  className="block px-3 py-2 rounded-md text-base font-medium text-muted-foreground hover:text-blue-600 hover:bg-accent transition-colors"
                  onClick={() => setIsOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
              <div className="border-t pt-4 mt-4">
                {isAuthenticated ? (
                  <>
                    <Link
                      to="/dashboard"
                      className="block px-3 py-2 text-base font-medium text-muted-foreground hover:text-foreground transition-colors"
                      onClick={() => setIsOpen(false)}
                    >
                      Dashboard
                    </Link>
                    <button
                      onClick={onLogout}
                      className="block w-full text-left px-3 py-2 text-base font-medium text-muted-foreground hover:text-foreground transition-colors"
                    >
                      Logout
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      to="/login"
                      className="block px-3 py-2 text-base font-medium text-muted-foreground hover:text-foreground transition-colors"
                      onClick={() => setIsOpen(false)}
                    >
                      Login
                    </Link>
                    <Link
                      to="/register"
                      className="block px-3 py-2 text-base font-medium text-blue-600 hover:text-blue-700 transition-colors"
                      onClick={() => setIsOpen(false)}
                    >
                      Get Started
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
