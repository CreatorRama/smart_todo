import { forwardRef } from 'react';
import clsx from 'clsx';

const Input = forwardRef(({ 
  className, 
  type = 'text', 
  error = false,
  ...props 
}, ref) => {
  return (
    <input
      type={type}
      className={clsx(
        'w-full px-3 py-2 border rounded-md shadow-sm transition-colors duration-200',
        'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
        error 
          ? 'border-red-300 focus:ring-red-500 focus:border-red-500' 
          : 'border-gray-300',
        'disabled:bg-gray-50 disabled:text-gray-500',
        className
      )}
      ref={ref}
      {...props}
    />
  );
});

Input.displayName = 'Input';

export default Input;