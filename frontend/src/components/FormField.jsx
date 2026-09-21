const inputClass =
  'mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500'

function FormField({ label, id, as = 'input', children, ...props }) {
  const Tag = as
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700">
        {label}
      </label>
      <Tag id={id} name={id} className={inputClass} {...props}>
        {children}
      </Tag>
    </div>
  )
}

export default FormField
