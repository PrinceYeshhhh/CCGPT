import type { Meta, StoryObj } from '@storybook/react';
import { Navbar } from './Navbar';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '../../contexts/ThemeContext';
import { AuthProvider } from '../../contexts/AuthContext';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const meta: Meta<typeof Navbar> = {
  title: 'Common/Navbar',
  component: Navbar,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ThemeProvider>
            <AuthProvider>
              <Story />
            </AuthProvider>
          </ThemeProvider>
        </BrowserRouter>
      </QueryClientProvider>
    ),
  ],
  argTypes: {
    isAuthenticated: {
      control: { type: 'boolean' },
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const NotAuthenticated: Story = {
  args: {
    isAuthenticated: false,
  },
};

export const Authenticated: Story = {
  args: {
    isAuthenticated: true,
  },
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ThemeProvider>
            <AuthProvider>
              <div className="min-h-screen">
                <Story />
                <div className="p-8">
                  <h1 className="text-2xl font-bold mb-4">Page Content</h1>
                  <p>This is the main content area below the navbar.</p>
                </div>
              </div>
            </AuthProvider>
          </ThemeProvider>
        </BrowserRouter>
      </QueryClientProvider>
    ),
  ],
};

export const MobileView: Story = {
  args: {
    isAuthenticated: false,
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ThemeProvider>
            <AuthProvider>
              <div className="min-h-screen">
                <Story />
                <div className="p-4">
                  <h1 className="text-xl font-bold mb-4">Mobile Content</h1>
                  <p>This is the mobile view of the navbar.</p>
                </div>
              </div>
            </AuthProvider>
          </ThemeProvider>
        </BrowserRouter>
      </QueryClientProvider>
    ),
  ],
};

export const WithUserDropdown: Story = {
  args: {
    isAuthenticated: true,
  },
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ThemeProvider>
            <AuthProvider>
              <div className="min-h-screen">
                <Story />
                <div className="p-8">
                  <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
                  <p>Click on the user menu to see the dropdown.</p>
                </div>
              </div>
            </AuthProvider>
          </ThemeProvider>
        </BrowserRouter>
      </QueryClientProvider>
    ),
  ],
};
