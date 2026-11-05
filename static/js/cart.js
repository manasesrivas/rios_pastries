(() => {
    const STORAGE_KEY = 'cart';

    // ---------- localStorage ----------
    const readCart = () => {
        try {
            const data = JSON.parse(localStorage.getItem(STORAGE_KEY));
            return Array.isArray(data) ? data : [];
        } catch {
            return [];
        }
    };

    const saveCart = (items) => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
        render();
    };

    // ---------- Utilidades ----------
    const money = (n) =>
        '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    const escapeHtml = (value) =>
        String(value ?? '').replace(/[&<>"']/g, (c) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[c]));

    // ---------- Acciones ----------
    const addItem = (product) => {
        const items = readCart();
        const existing = items.find((i) => i.id === product.id);
        const max = product.stock > 0 ? product.stock : Infinity;
        const quantity = Math.min(Math.max(1, product.quantity || 1), max);

        if (existing) {
            existing.quantity = quantity; // asigna el valor del contador, no suma
        } else {
            items.push({ ...product, quantity });
        }
        saveCart(items);
    };

    const changeQuantity = (id, delta) => {
        const items = readCart();
        const item = items.find((i) => i.id === id);
        if (!item) return;

        const max = item.stock > 0 ? item.stock : Infinity;
        item.quantity = Math.min(max, Math.max(1, item.quantity + delta));
        saveCart(items);
    };

    const removeItem = (id) => saveCart(readCart().filter((i) => i.id !== id));
    const clearCart = () => saveCart([]);

    // ---------- Modal ----------
    const modal = document.getElementById('cart-modal');

    const openModal = () => {
        if (!modal) return;
        render();
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    };

    const closeModal = () => {
        if (!modal) return;
        modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    };

    // ---------- Render ----------
    const cellBase =
        'flex items-center justify-between gap-4 py-2 md:table-cell md:px-4 md:py-3 ' +
        'before:text-xs before:font-semibold before:uppercase before:text-gray-500 ' +
        'before:content-[attr(data-label)] md:before:content-none';

    const rowTemplate = (item) => {
        const subtotal = item.price * item.quantity;
        const image = item.image
            ? `<img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.name)}" class="h-16 w-16 rounded-lg border border-gray-200 object-cover">`
            : `<div class="flex h-16 w-16 items-center justify-center rounded-lg border border-gray-200 bg-gray-100 text-xs text-gray-400">Sin imagen</div>`;
        const imageUrl = item.image
            ? `<a href="${escapeHtml(item.image)}" target="_blank" rel="noopener" class="hidden max-w-[10rem] truncate text-xs text-indigo-600 hover:underline lg:block">${escapeHtml(item.image)}</a>`
            : '';

        return `
        <tr class="block border-b border-gray-200 p-4 md:table-row md:p-0" data-id="${escapeHtml(item.id)}">
            <td data-label="Imagen" class="${cellBase}">
                <div class="flex flex-col items-end gap-1 md:items-start">${image}${imageUrl}</div>
            </td>
            <td data-label="Producto" class="${cellBase} font-semibold text-gray-900">
                <span class="text-right md:text-left">${escapeHtml(item.name)}</span>
            </td>
            <td data-label="Categoría" class="${cellBase} text-gray-600">
                <span>${escapeHtml(item.category)}</span>
            </td>
            <td data-label="Precio" class="${cellBase} text-gray-700">
                <span>${money(item.price)}</span>
            </td>
            <td data-label="Cantidad" class="${cellBase}">
                <div class="inline-flex overflow-hidden rounded-lg border border-gray-300">
                    <button type="button" data-action="minus" aria-label="Reducir cantidad"
                            class="h-9 w-9 bg-gray-50 text-lg text-gray-700 hover:bg-gray-100">-</button>
                    <span class="flex h-9 min-w-10 items-center justify-center bg-white px-2 font-semibold text-gray-900">${item.quantity}</span>
                    <button type="button" data-action="plus" aria-label="Aumentar cantidad"
                            class="h-9 w-9 bg-gray-50 text-lg text-gray-700 hover:bg-gray-100">+</button>
                </div>
            </td>
            <td data-label="Subtotal" class="${cellBase} font-semibold text-indigo-700">
                <span>${money(subtotal)}</span>
            </td>
            <td data-label="" class="${cellBase} md:text-right">
                <button type="button" data-action="remove"
                        class="rounded-lg px-3 py-1.5 text-sm font-semibold text-red-600 hover:bg-red-50">Quitar</button>
            </td>
        </tr>`;
    };

    // ----- checkout -----
    const checkout = async (url) => {
        const items = readCart();
        if (items.length === 0) return;

        const formData = new FormData();
        items.forEach((item) => {
            formData.append('product_id', item.id);
            formData.append('quantity', item.quantity);
        });

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });

            if (!response.ok) throw new Error('Error ' + response.status);

            clearCart();
            closeModal();
            // window.location.href = '/orders/';  // opcional: redirigir
        } catch (error) {
            console.error('No se pudo enviar el carrito:', error);
            alert('No se pudo realizar el pedido. Intenta de nuevo.');
        }
    };

    function render() {
        const items = readCart();
        const total = items.reduce((sum, i) => sum + i.price * i.quantity, 0);
        const count = items.reduce((sum, i) => sum + i.quantity, 0);

        document.querySelectorAll('[data-cart-count]').forEach((el) => (el.textContent = count));

        const body = document.getElementById('cart-body');
        const table = document.getElementById('cart-table');
        const empty = document.getElementById('cart-empty');
        const totalEl = document.getElementById('cart-total');
        if (!body || !table || !empty || !totalEl) return;

        body.innerHTML = items.map(rowTemplate).join('');
        table.classList.toggle('hidden', items.length === 0);
        empty.classList.toggle('hidden', items.length > 0);
        totalEl.textContent = money(total);
    }

    // ---------- Eventos ----------
    document.addEventListener('click', (e) => {
        const addBtn = e.target.closest('[data-add-to-cart]');
        const qtyInput = document.getElementById('quantity');
        if (addBtn) {
            const d = addBtn.dataset;
            addItem({
                id: d.id,
                name: d.name,
                category: d.category,
                price: Number(d.price) || 0,
                image: d.image || '',
                quantity: qtyInput ? Number(qtyInput.value) || 1 : 1,
            });
            alert('se ha agregado al carrito')
            return;
        }

        if (e.target.closest('[data-cart-open]')) return openModal();
        if (e.target.closest('[data-cart-close]')) return closeModal();
        if (e.target.closest('[data-cart-clear]')) return clearCart();

        const actionBtn = e.target.closest('[data-action]');
        if (actionBtn) {
            const id = actionBtn.closest('tr')?.dataset.id;
            if (!id) return;
            const action = actionBtn.dataset.action;
            if (action === 'plus') changeQuantity(id, 1);
            if (action === 'minus') changeQuantity(id, -1);
            if (action === 'remove') removeItem(id);
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });

    // Sincroniza entre pestañas
    window.addEventListener('storage', (e) => {
        if (e.key === STORAGE_KEY) render();
    });

    document.addEventListener('DOMContentLoaded', render);
})();