import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'

interface ErrorFallbackProps {
  error: Error
  resetError: () => void
  componentName?: string
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({ 
  error, 
  resetError, 
  componentName = 'component' 
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-6 bg-red-50 border border-red-200 rounded-lg">
      <div className="flex items-center justify-center w-10 h-10 bg-red-100 rounded-full mb-3">
        <AlertCircle className="w-5 h-5 text-red-600" />
      </div>
      
      <h3 className="text-sm font-medium text-red-800 mb-2">
        {componentName} Error
      </h3>
      
      <p className="text-sm text-red-600 text-center mb-4">
        {error.message || 'Something went wrong'}
      </p>
      
      <button
        onClick={resetError}
        className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
      >
        <RefreshCw className="w-4 h-4 mr-2" />
        Try Again
      </button>
    </div>
  )
}

export default ErrorFallback
