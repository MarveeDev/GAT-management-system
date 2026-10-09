import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import { Check, ChevronDown, Search, X } from 'lucide-react'

import type { Product } from '../../types'

interface ProductSearchSelectProps {
  inputId?: string
  products: Product[]
  stockByProductAndShop: Map<string, Map<string, number>>
  effectiveShopId: string
  value: string
  onChange: (productId: string) => void
}

const inputClass =
  'w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-9 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30'

export default function ProductSearchSelect({
  inputId,
  products,
  stockByProductAndShop,
  effectiveShopId,
  value,
  onChange,
}: ProductSearchSelectProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const rootRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const listboxId = inputId ? `${inputId}-listbox` : 'product-search-listbox'

  const selectedProduct = useMemo(
    () => products.find((product) => product.id === value) ?? null,
    [products, value],
  )

  const results = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return products
    return products.filter((product) => product.name.toLowerCase().includes(q))
  }, [products, query])

  const displayValue = open ? query : (selectedProduct?.name ?? '')

  function stockFor(productId: string): number {
    return stockByProductAndShop.get(productId)?.get(effectiveShopId) ?? 0
  }

  function openList() {
    setOpen(true)
    setQuery('')
    setActiveIndex(0)
  }

  function closeList() {
    setOpen(false)
    setQuery('')
  }

  function selectProduct(productId: string) {
    onChange(productId)
    closeList()
    inputRef.current?.blur()
  }

  useEffect(() => {
    function onDocumentMouseDown(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        closeList()
      }
    }
    document.addEventListener('mousedown', onDocumentMouseDown)
    return () => document.removeEventListener('mousedown', onDocumentMouseDown)
  }, [])

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      if (!open) {
        openList()
        return
      }
      setActiveIndex((index) => (results.length ? (index + 1) % results.length : 0))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      if (!open) {
        openList()
        return
      }
      setActiveIndex((index) =>
        results.length ? (index - 1 + results.length) % results.length : 0,
      )
    } else if (event.key === 'Enter') {
      event.preventDefault()
      if (open && results.length > 0) {
        const item = results[Math.min(activeIndex, results.length - 1)]
        if (item) selectProduct(item.id)
      } else {
        openList()
      }
    } else if (event.key === 'Escape') {
      event.preventDefault()
      closeList()
      inputRef.current?.blur()
    } else if (event.key === 'Tab') {
      closeList()
    }
  }

  return (
    <div ref={rootRef} className="relative">
      <Search
        className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
        aria-hidden="true"
      />
      <input
        ref={inputRef}
        id={inputId}
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-autocomplete="list"
        autoComplete="off"
        value={displayValue}
        placeholder="Search product name or SKU..."
        onFocus={openList}
        onChange={(event) => {
          setQuery(event.target.value)
          setActiveIndex(0)
          if (!open) setOpen(true)
        }}
        onKeyDown={handleKeyDown}
        className={inputClass}
      />
      {value && !open ? (
        <button
          type="button"
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => onChange('')}
          aria-label="Clear product selection"
          className="absolute right-2 top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      ) : (
        <ChevronDown
          className={`pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-transform ${
            open ? 'rotate-180' : ''
          }`}
          aria-hidden="true"
        />
      )}

      {open && (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute z-20 mt-1 max-h-64 w-full overflow-y-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg"
        >
          {results.length === 0 ? (
            <li className="px-3 py-2 text-sm text-slate-500">
              {query.trim() ? 'No products match your search.' : 'No products available.'}
            </li>
          ) : (
            results.map((product, index) => {
              const stock = stockFor(product.id)
              const isSelected = product.id === value
              const isActive = index === activeIndex
              return (
                <li
                  key={product.id}
                  id={`${listboxId}-option-${index}`}
                  role="option"
                  aria-selected={isSelected}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => selectProduct(product.id)}
                  onMouseEnter={() => setActiveIndex(index)}
                  className={`flex cursor-pointer items-center justify-between gap-2 px-3 py-2 text-sm ${
                    isActive ? 'bg-brand-50' : ''
                  } ${isSelected ? 'text-slate-900' : 'text-slate-700'}`}
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium">{product.name}</span>
                    {product.category && (
                      <span className="block truncate text-xs text-slate-500">
                        {product.category}
                      </span>
                    )}
                  </span>
                  <span
                    className={`shrink-0 text-xs ${
                      stock <= 0 ? 'text-danger-600' : 'text-slate-500'
                    }`}
                  >
                    {stock} in stock
                  </span>
                  {isSelected && (
                    <Check className="h-4 w-4 shrink-0 text-brand-600" aria-hidden="true" />
                  )}
                </li>
              )
            })
          )}
        </ul>
      )}
    </div>
  )
}
