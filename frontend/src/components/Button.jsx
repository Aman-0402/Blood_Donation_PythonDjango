const variants = {
  primary: 'bg-red-600 text-white hover:bg-red-700',
  secondary: 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
  danger: 'border border-red-300 bg-white text-red-700 hover:bg-red-50',
}

function Button({ variant = 'primary', className = '', ...props }) {
  return (
    <button
      type="button"
      className={`rounded-md px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`}
      {...props}
    />
  )
}

export default Button
