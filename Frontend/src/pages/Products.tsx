import { useCallback, useEffect, useMemo, useState } from 'react'
import { CircleAlert, CircleCheck, CircleX, Package, Plus } from 'lucide-react'

import EmptyState from '../components/EmptyState'
import ErrorMessage from '../components/ErrorMessage'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'
import StatCard from '../components/dashboard/StatCard'
import ProductFilters, {
  type ProductStatusFilter,
  type StockFilter,
} from '../components/products/ProductFilters'
import ProductForm, { type ProductFormValues } from '../components/products/ProductForm'
import ProductTable from '../components/products/ProductTable'
import StockAdjustForm from '../components/products/StockAdjustForm'
import { useAuth } from '../contexts/authContext'
import { listInventory, setInventory } from '../services/inventoryService'
import { createProduct, listProducts, updateProduct } from '../services/productService'
import { listShops } from '../services/shopService'
import type { Inventory, Product, Shop } from '../types'
import { LOW_STOCK_THRESHOLD } from '../utils/inventory'

export default function Products() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'SUPER_ADMIN'

  const [products, setProducts] = useState<Product[] | null>(null)
  const [inventory, setInventoryRows] = useState<Inventory[]>([])
  const [shops, setShops] = useState<Shop[]>([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const [search, setSearch] = useState('')
  const [stockFilter, setStockFilter] = useState<StockFilter>('ALL')
  const [statusFilter, setStatusFilter] = useState<ProductStatusFilter>('ALL')
  const [selectedShopId, setSelectedShopId] = useState('ALL')

  const [formOpen, setFormOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [adjustProduct, setAdjustProduct] = useState<Product | null>(null)

  const [success, setSuccess] = useState<string | null>(null)
  const [warning, setWarning] = useState<string | null>(null)

  const viewShopId = isSuperAdmin ? selectedShopId : (user?.shop_id ?? '')

  const loadData = useCallback(async () => {
    const [productsRes, inventoryRes] = await Promise.all([listProducts(), listInventory()])
    return { products: productsRes.products, inventory: inventoryRes.inventory }
  }, [])

  useEffect(() => {
    let active = true
    loadData()
      .then((res) => {
        if (!active) return
        setProducts(res.products)
        setInventoryRows(res.inventory)
        setError(null)
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unable to load products and inventory.')
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [loadData, reloadToken])

  useEffect(() => {
    let active = true
    listShops()
      .then((res) => {
        if (active) setShops(res.shops)
      })
      .catch(() => {
        // shop list is best-effort; the page still works without it
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!success) return
    const timer = setTimeout(() => setSuccess(null), 4000)
    return () => clearTimeout(timer)
  }, [success])

  useEffect(() => {
    if (!warning) return
    const timer = setTimeout(() => setWarning(null), 6000)
    return () => clearTimeout(timer)
  }, [warning])

  const inventoryByProduct = useMemo(() => {
    const map = new Map<string, Map<string, number>>()
    for (const row of inventory) {
      let byShop = map.get(row.product_id)
      if (!byShop) {
        byShop = new Map()
        map.set(row.product_id, byShop)
      }
      byShop.set(row.shop_id, row.quantity)
    }
    return map
  }, [inventory])

  const viewStock = useMemo(() => {
    const result = new Map<string, number>()
    for (const product of products ?? []) {
      const byShop = inventoryByProduct.get(product.id)
      let quantity = 0
      if (viewShopId === 'ALL') {
        if (byShop) {
          for (const q of byShop.values()) quantity += q
        }
      } else {
        quantity = byShop?.get(viewShopId) ?? 0
      }
      result.set(product.id, quantity)
    }
    return result
  }, [products, inventoryByProduct, viewShopId])

  const summary = useMemo(() => {
    const items = products ?? []
    let inStock = 0
    let lowStock = 0
    let outOfStock = 0
    for (const product of items) {
      const quantity = viewStock.get(product.id) ?? 0
      if (quantity === 0) {
        outOfStock += 1
      } else {
        inStock += 1
        if (quantity <= LOW_STOCK_THRESHOLD) lowStock += 1
      }
    }
    return { total: items.length, inStock, lowStock, outOfStock }
  }, [products, viewStock])

  const visibleProducts = useMemo(() => {
    if (!products) return []
    const query = search.trim().toLowerCase()
    return products.filter((product) => {
      if (isSuperAdmin && statusFilter !== 'ALL' && product.status !== statusFilter) return false
      if (!isSuperAdmin && product.status !== 'ACTIVE') return false
      if (query && !`${product.name} ${product.category ?? ''}`.toLowerCase().includes(query)) {
        return false
      }
      const quantity = viewStock.get(product.id) ?? 0
      if (stockFilter === 'IN_STOCK' && quantity <= 0) return false
      if (stockFilter === 'LOW_STOCK' && !(quantity > 0 && quantity <= LOW_STOCK_THRESHOLD)) {
        return false
      }
      if (stockFilter === 'OUT_OF_STOCK' && quantity !== 0) return false
      return true
    })
  }, [products, search, stockFilter, statusFilter, isSuperAdmin, viewStock])

  const assignedShopName = useMemo(
    () => (isSuperAdmin ? null : (shops.find((s) => s.id === user?.shop_id)?.name ?? null)),
    [shops, isSuperAdmin, user?.shop_id],
  )

  const activeShops = useMemo(() => shops.filter((shop) => shop.status === 'ACTIVE'), [shops])

  const shopNames = useMemo(() => new Map(shops.map((shop) => [shop.id, shop.name])), [shops])

  function openCreate() {
    setEditingProduct(null)
    setFormOpen(true)
  }

  function openEdit(product: Product) {
    setEditingProduct(product)
    setFormOpen(true)
  }

  function retry() {
    setLoading(true)
    setError(null)
    setReloadToken((t) => t + 1)
  }

  function closeForm() {
    setFormOpen(false)
    setEditingProduct(null)
  }

  async function handleCreate(values: ProductFormValues) {
    const res = await createProduct({
      name: values.name,
      category: values.category || undefined,
      minimum_price: values.minimum_price,
      maximum_price: values.maximum_price,
      status: values.status,
    })
    const productId = res.product.id

    const stockEntries = (values.initial_stock ?? []).filter((entry) => entry.quantity > 0)
    const failedShops: string[] = []
    for (const entry of stockEntries) {
      try {
        await setInventory({
          product_id: productId,
          shop_id: entry.shop_id,
          quantity: entry.quantity,
        })
      } catch {
        failedShops.push(shopNames.get(entry.shop_id) ?? entry.shop_id)
      }
    }

    closeForm()
    setReloadToken((t) => t + 1)

    if (failedShops.length > 0) {
      setWarning(
        `Product created, but initial stock could not be set for: ${failedShops.join(', ')}.`,
      )
    } else if (stockEntries.length > 0) {
      setSuccess('Product created successfully. Initial stock has been set for all selected shops.')
    } else {
      setSuccess('Product created successfully.')
    }
  }

  async function handleEdit(values: ProductFormValues) {
    if (!editingProduct) return
    await updateProduct(editingProduct.id, {
      name: values.name,
      category: values.category || undefined,
      minimum_price: values.minimum_price,
      maximum_price: values.maximum_price,
      status: values.status,
    })
    setSuccess('Product updated successfully.')
    closeForm()
    setReloadToken((t) => t + 1)
  }

  async function handleAdjustStock(quantity: number) {
    if (!adjustProduct) return
    await setInventory({
      product_id: adjustProduct.id,
      shop_id: viewShopId,
      quantity,
    })
    setSuccess(`Stock updated for ${adjustProduct.name}.`)
    setAdjustProduct(null)
    setReloadToken((t) => t + 1)
  }

  const adjustShopName = adjustProduct
    ? (shops.find((s) => s.id === viewShopId)?.name ?? 'Selected shop')
    : ''
  const adjustCurrentQuantity = adjustProduct
    ? (inventoryByProduct.get(adjustProduct.id)?.get(viewShopId) ?? 0)
    : 0

  const summaryLoading = loading && products === null
  const summaryError = error

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Products &amp; Inventory</h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage products, pricing and shop stock.
          </p>
        </div>
        {isSuperAdmin && (
          <button
            type="button"
            onClick={openCreate}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            Add Product
          </button>
        )}
      </header>

      {success && (
        <div
          role="status"
          className="rounded-lg border border-success-600/20 bg-success-50 px-4 py-3 text-sm text-success-700"
        >
          {success}
        </div>
      )}

      {warning && (
        <div
          role="status"
          className="rounded-lg border border-warning-500/30 bg-warning-50 px-4 py-3 text-sm text-slate-700"
        >
          {warning}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total Products"
          icon={Package}
          accent="blue"
          section={{ loading: summaryLoading, error: summaryError, data: summary.total }}
        />
        <StatCard
          label="In Stock"
          icon={CircleCheck}
          accent="green"
          section={{ loading: summaryLoading, error: summaryError, data: summary.inStock }}
        />
        <StatCard
          label="Low Stock"
          icon={CircleAlert}
          accent="purple"
          section={{ loading: summaryLoading, error: summaryError, data: summary.lowStock }}
        />
        <StatCard
          label="Out of Stock"
          icon={CircleX}
          accent="red"
          section={{ loading: summaryLoading, error: summaryError, data: summary.outOfStock }}
        />
      </div>

      <ProductFilters
        search={search}
        onSearchChange={setSearch}
        stock={stockFilter}
        onStockChange={setStockFilter}
        status={statusFilter}
        onStatusChange={setStatusFilter}
        shop={selectedShopId}
        onShopChange={setSelectedShopId}
        shops={shops}
        showShopSelector={isSuperAdmin}
        showStatusFilter={isSuperAdmin}
      />

      {!isSuperAdmin && assignedShopName && (
        <p className="text-sm text-slate-500">
          Showing inventory for <span className="font-medium text-slate-700">{assignedShopName}</span>.
        </p>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="space-y-3">
          <ErrorMessage message={error} />
          <button
            type="button"
            onClick={retry}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            Retry
          </button>
        </div>
      ) : !products || products.length === 0 ? (
        <EmptyState
          title="No products yet"
          description={
            isSuperAdmin
              ? 'Add your first product to start tracking inventory.'
              : 'No products are available for your shop.'
          }
        />
      ) : visibleProducts.length === 0 ? (
        <EmptyState title="No matching products" description="No products match your search or filters." />
      ) : (
        <ProductTable
          products={visibleProducts}
          shops={shops}
          selectedShopId={viewShopId}
          inventoryByProduct={inventoryByProduct}
          isSuperAdmin={isSuperAdmin}
          onEdit={isSuperAdmin ? openEdit : undefined}
          onAdjustStock={isSuperAdmin && viewShopId !== 'ALL' ? setAdjustProduct : undefined}
        />
      )}

      {formOpen && (
        <Modal title={editingProduct ? 'Edit Product' : 'Add Product'} onClose={closeForm}>
          <ProductForm
            key={editingProduct?.id ?? 'new'}
            initial={editingProduct ?? undefined}
            shops={activeShops}
            stockByShop={editingProduct ? inventoryByProduct.get(editingProduct.id) : undefined}
            initialShopId={editingProduct && viewShopId !== 'ALL' ? viewShopId : undefined}
            onSubmit={editingProduct ? handleEdit : handleCreate}
            onCancel={closeForm}
          />
        </Modal>
      )}

      {adjustProduct && (
        <Modal title="Adjust Stock" onClose={() => setAdjustProduct(null)}>
          <StockAdjustForm
            product={adjustProduct}
            shopName={adjustShopName}
            currentQuantity={adjustCurrentQuantity}
            onSubmit={handleAdjustStock}
            onCancel={() => setAdjustProduct(null)}
          />
        </Modal>
      )}
    </div>
  )
}
