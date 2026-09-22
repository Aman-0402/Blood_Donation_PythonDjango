function Container({ as: Tag = 'div', className = '', children }) {
  return <Tag className={`mx-auto w-full max-w-[1450px] px-4 sm:px-6 lg:px-8 ${className}`}>{children}</Tag>
}

export default Container
