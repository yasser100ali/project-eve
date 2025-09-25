# Eve Project

A powerful AI chatbot application built with Next.js and FastAPI, designed for intelligent conversations, data analysis, and interactive AI experiences.

## Features

- **Advanced AI Chatbot**
  - Real-time streaming conversations with AI models
  - Support for multiple AI providers (OpenAI, xAI, and more)
  - Interactive data analysis and visualization capabilities
  - File upload and processing (CSV, Excel, documents)
  
- **Modern Web Architecture**
  - [Next.js 15](https://nextjs.org) frontend with App Router for optimal performance
  - Python FastAPI backend for robust AI processing
  - Real-time streaming responses for enhanced user experience
  
- **AI Integration**
  - [AI SDK](https://ai-sdk.dev/docs/introduction) with unified API for LLMs
  - Multiple model providers through Vercel AI Gateway
  - Web search capabilities for comprehensive research
  - Code interpretation and execution environment

- **Modern UI/UX**
  - [shadcn/ui](https://ui.shadcn.com) components with [Tailwind CSS](https://tailwindcss.com)
  - Dark/light theme support with system preference detection
  - Responsive design optimized for all devices

- **Data Management**
  - PostgreSQL database with Drizzle ORM for chat history
  - File storage capabilities for document processing
  - Secure authentication with [Auth.js](https://authjs.dev)

## Model Providers

This application uses the [Vercel AI Gateway](https://vercel.com/docs/ai-gateway) to access multiple AI models through a unified interface. The default configuration includes [xAI](https://x.ai) models (`grok-2-vision-1212`, `grok-3-mini`) routed through the gateway.

### AI Gateway Authentication

**For Vercel deployments**: Authentication is handled automatically via OIDC tokens.

**For non-Vercel deployments**: You need to provide an AI Gateway API key by setting the `AI_GATEWAY_API_KEY` environment variable in your `.env.local` file.

With the [AI SDK](https://ai-sdk.dev/docs/introduction), you can also switch to direct LLM providers like [OpenAI](https://openai.com), [Anthropic](https://anthropic.com), [Cohere](https://cohere.com/), and [many more](https://ai-sdk.dev/providers/ai-sdk-providers) with just a few lines of code.

## Architecture Overview

Eve Project uses a modern full-stack architecture:

### Frontend (Next.js)
- Built with Next.js 15 and React 19
- App Router for optimal performance and SEO
- Real-time chat interface with streaming responses
- File upload support for data analysis
- Responsive design with dark/light theme support

### Backend (Python FastAPI)
- AI processing using multiple LLM providers
- Streaming API responses for real-time chat
- Web search integration for comprehensive research
- Data analysis capabilities for various file formats
- RESTful API design with proper error handling

### Key Components
- **Authentication**: Secure user management with NextAuth.js
- **Database**: PostgreSQL with Drizzle ORM for chat history
- **File Storage**: Support for document and data file processing
- **AI Integration**: Multiple AI providers with unified interface
- **UI Components**: shadcn/ui with Tailwind CSS for modern interface

## Running Locally

Eve Project consists of both a Next.js frontend and a Python FastAPI backend. You'll need to set up environment variables for both components.

### Prerequisites

- Node.js 18+ and pnpm
- Python 3.8+
- AI API keys (OpenAI, xAI, or other providers)

### Environment Setup

1. **Clone the repository and navigate to the project directory**
2. **Copy environment variables**: `cp .env.example .env.local`
3. **Edit `.env.local`** with your API keys and configuration

### Frontend Setup (Next.js)

```bash
# Install dependencies
pnpm install

# Start the development server
pnpm dev
```

### Backend Setup (Python FastAPI)

If you need to run the backend separately:

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_openai_api_key_here
export XAI_API_KEY=your_xai_api_key_here

# Run the backend server
uvicorn main:app --reload --port 8000
```

### Full Development Environment

For the complete development experience with both frontend and backend:

```bash
# This runs both frontend (port 3000) and backend (port 8000)
pnpm dev
```

Your Eve Project application will be available at [localhost:3000](http://localhost:3000).

> **Security Note:** Never commit your `.env.local` file or expose your API keys in version control.
