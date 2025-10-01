import type { Meta, StoryObj } from '@storybook/react';
import { OptimizedImage, useBlurDataURL, generateImageSizes, COMMON_BREAKPOINTS } from './optimized-image';

const meta: Meta<typeof OptimizedImage> = {
  title: 'UI/OptimizedImage',
  component: OptimizedImage,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    src: {
      control: { type: 'text' },
    },
    alt: {
      control: { type: 'text' },
    },
    width: {
      control: { type: 'number' },
    },
    height: {
      control: { type: 'number' },
    },
    quality: {
      control: { type: 'range', min: 1, max: 100, step: 1 },
    },
    loading: {
      control: { type: 'select' },
      options: ['lazy', 'eager'],
    },
    priority: {
      control: { type: 'boolean' },
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// Sample images for testing
const sampleImages = {
  landscape: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop',
  portrait: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=600&fit=crop',
  square: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop',
  avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face',
};

export const Default: Story = {
  args: {
    src: sampleImages.landscape,
    alt: 'Beautiful landscape',
    width: 400,
    height: 300,
  },
};

export const LazyLoading: Story = {
  args: {
    src: sampleImages.landscape,
    alt: 'Lazy loaded image',
    width: 400,
    height: 300,
    loading: 'lazy',
  },
};

export const EagerLoading: Story = {
  args: {
    src: sampleImages.landscape,
    alt: 'Eager loaded image',
    width: 400,
    height: 300,
    loading: 'eager',
    priority: true,
  },
};

export const WithBlurPlaceholder: Story = {
  args: {
    src: sampleImages.landscape,
    alt: 'Image with blur placeholder',
    width: 400,
    height: 300,
    placeholder: 'blur',
    blurDataURL: 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAIAAoDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAhEAACAQMDBQAAAAAAAAAAAAABAgMABAUGIWGRkqGx0f/EABUBAQEAAAAAAAAAAAAAAAAAAAMF/8QAGhEAAgIDAAAAAAAAAAAAAAAAAAECEgMRkf/aAAwDAQACEQMRAD8AltJagyeH0AthI5xdrLcNM91BF5pX2HaH9bcfaSXWGaRmknyJckliyjqTzSlT54b6bk+h0R//2Q==',
  },
};

export const Avatar: Story = {
  args: {
    src: sampleImages.avatar,
    alt: 'User avatar',
    width: 100,
    height: 100,
    className: 'rounded-full',
  },
};

export const Responsive: Story = {
  args: {
    src: sampleImages.landscape,
    alt: 'Responsive image',
    width: 800,
    height: 600,
    sizes: generateImageSizes(COMMON_BREAKPOINTS),
  },
  render: (args) => (
    <div className="w-full max-w-4xl">
      <OptimizedImage {...args} className="w-full h-auto" />
    </div>
  ),
};

export const WithErrorFallback: Story = {
  args: {
    src: 'https://invalid-url.com/image.jpg',
    alt: 'Image with error',
    width: 400,
    height: 300,
    fallback: (
      <div className="flex items-center justify-center h-full bg-muted text-muted-foreground">
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p>Image not available</p>
        </div>
      </div>
    ),
  },
};

export const Gallery: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <OptimizedImage
        src={sampleImages.landscape}
        alt="Landscape 1"
        width={300}
        height={200}
        className="rounded-lg"
      />
      <OptimizedImage
        src={sampleImages.portrait}
        alt="Portrait 1"
        width={300}
        height={400}
        className="rounded-lg"
      />
      <OptimizedImage
        src={sampleImages.square}
        alt="Square 1"
        width={300}
        height={300}
        className="rounded-lg"
      />
    </div>
  ),
};

export const PerformanceComparison: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Regular Image (No Optimization)</h3>
        <img
          src={sampleImages.landscape}
          alt="Regular image"
          width={400}
          height={300}
          className="rounded-lg"
        />
      </div>
      <div>
        <h3 className="text-lg font-semibold mb-4">Optimized Image (With Lazy Loading)</h3>
        <OptimizedImage
          src={sampleImages.landscape}
          alt="Optimized image"
          width={400}
          height={300}
          className="rounded-lg"
          loading="lazy"
        />
      </div>
    </div>
  ),
};
