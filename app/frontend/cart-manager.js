/**
 * SISTEMA DE CARRITO INDIVIDUAL POR USUARIO
 * Soluciona el problema de carrito compartido entre usuarios
 * Cada usuario tendrá su carrito individual basado en su email/ID
 */

class CartManager {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    async init() {
        await this.loadCurrentUser();
    }

    async loadCurrentUser() {
        const token = localStorage.getItem('token');
        if (!token) return null;

        try {
            const response = await fetch('/api/v1/accesos/me', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                this.currentUser = await response.json();
                return this.currentUser;
            }
        } catch (error) {
            console.error('Error al cargar usuario:', error);
        }
        return null;
    }

    getUserCartKey(type = 'productos') {
        if (!this.currentUser) return null;
        
        // Usar email como identificador único del usuario
        const userIdentifier = this.currentUser.email || this.currentUser.sub || 'anonymous';
        return `cart_${type}_${userIdentifier}`;
    }

    // ========== GESTIÓN DE CARRITO DE PRODUCTOS ==========
    
    getProductCart() {
        const cartKey = this.getUserCartKey('productos');
        if (!cartKey) return [];
        
        const cartData = localStorage.getItem(cartKey);
        return cartData ? JSON.parse(cartData) : [];
    }

    saveProductCart(cart) {
        const cartKey = this.getUserCartKey('productos');
        if (!cartKey) return false;
        
        localStorage.setItem(cartKey, JSON.stringify(cart));
        return true;
    }

    addProductToCart(product) {
        if (!this.currentUser) {
            alert('Debes estar autenticado para agregar productos al carrito');
            return false;
        }

        let cart = this.getProductCart();
        const existingIndex = cart.findIndex(item => item.codigo === product.codigo);

        if (existingIndex >= 0) {
            // Verificar stock disponible
            const newQuantity = cart[existingIndex].cantidad + (product.cantidad || 1);
            if (newQuantity > product.stockDisponible) {
                alert(`Solo hay ${product.stockDisponible} unidades disponibles en stock`);
                return false;
            }
            cart[existingIndex].cantidad = newQuantity;
        } else {
            cart.push({
                codigo: product.codigo,
                idProducto: product.idProducto,
                nombre: product.nombre,
                categoria: product.categoria,
                precio: product.precio || 0,
                cantidad: product.cantidad || 1,
                stockDisponible: product.stockDisponible
            });
        }

        this.saveProductCart(cart);
        this.updateCartCountDisplay();
        return true;
    }

    removeProductFromCart(codigo) {
        let cart = this.getProductCart();
        cart = cart.filter(item => item.codigo !== codigo);
        this.saveProductCart(cart);
        this.updateCartCountDisplay();
    }

    updateProductQuantity(codigo, newQuantity) {
        let cart = this.getProductCart();
        const itemIndex = cart.findIndex(item => item.codigo === codigo);
        
        if (itemIndex >= 0) {
            if (newQuantity <= 0) {
                this.removeProductFromCart(codigo);
            } else if (newQuantity > cart[itemIndex].stockDisponible) {
                alert(`Solo hay ${cart[itemIndex].stockDisponible} unidades disponibles`);
                return false;
            } else {
                cart[itemIndex].cantidad = newQuantity;
                this.saveProductCart(cart);
                this.updateCartCountDisplay();
            }
        }
        return true;
    }

    clearProductCart() {
        const cartKey = this.getUserCartKey('productos');
        if (cartKey) {
            localStorage.removeItem(cartKey);
            this.updateCartCountDisplay();
        }
    }

    // ========== GESTIÓN DE CARRITO DE CATEGORÍAS ==========
    
    getCategoryCart() {
        const cartKey = this.getUserCartKey('categorias');
        if (!cartKey) return [];
        
        const cartData = localStorage.getItem(cartKey);
        return cartData ? JSON.parse(cartData) : [];
    }

    saveCategoryCart(cart) {
        const cartKey = this.getUserCartKey('categorias');
        if (!cartKey) return false;
        
        localStorage.setItem(cartKey, JSON.stringify(cart));
        return true;
    }

    addCategoryToCart(category) {
        if (!this.currentUser) {
            alert('Debes estar autenticado para agregar categorías al carrito');
            return false;
        }

        let cart = this.getCategoryCart();
        const existingIndex = cart.findIndex(item => item.codigo === category.codigo);

        if (existingIndex >= 0) {
            alert('Esta categoría ya está en tu carrito');
            return false;
        }

        cart.push({
            codigo: category.codigo,
            idCategoria: category.idCategoria,
            nombre: category.nombre,
            descripcion: category.descripcion
        });

        this.saveCategoryCart(cart);
        this.updateCartCountDisplay();
        return true;
    }

    removeCategoryFromCart(codigo) {
        let cart = this.getCategoryCart();
        cart = cart.filter(item => item.codigo !== codigo);
        this.saveCategoryCart(cart);
        this.updateCartCountDisplay();
    }

    clearCategoryCart() {
        const cartKey = this.getUserCartKey('categorias');
        if (cartKey) {
            localStorage.removeItem(cartKey);
            this.updateCartCountDisplay();
        }
    }

    // ========== FUNCIONES DE INTERFAZ ==========
    
    updateCartCountDisplay() {
        const productCount = this.getProductCart().length;
        const categoryCount = this.getCategoryCart().length;
        const totalCount = productCount + categoryCount;

        // Actualizar contador en la interfaz
        const cartCountElements = document.querySelectorAll('.cart-count, #cart-count');
        cartCountElements.forEach(element => {
            if (totalCount > 0) {
                element.textContent = totalCount;
                element.style.display = 'block';
            } else {
                element.style.display = 'none';
            }
        });

        // Actualizar total de productos en el modal
        const cartTotalElements = document.querySelectorAll('#cart-total');
        cartTotalElements.forEach(element => {
            element.textContent = totalCount;
        });
    }

    // ========== LIMPIEZA AL CERRAR SESIÓN ==========
    
    clearAllUserCarts() {
        this.clearProductCart();
        this.clearCategoryCart();
        this.currentUser = null;
    }

    // ========== MIGRACIÓN DE CARRITOS EXISTENTES ==========
    
    async migrateOldCarts() {
        // Migrar carrito de productos existente
        const oldProductCart = localStorage.getItem('cart');
        if (oldProductCart && this.currentUser) {
            const cartKey = this.getUserCartKey('productos');
            if (cartKey && !localStorage.getItem(cartKey)) {
                localStorage.setItem(cartKey, oldProductCart);
                localStorage.removeItem('cart');
                console.log('Carrito de productos migrado exitosamente');
            }
        }

        // Migrar carrito de categorías existente
        const oldCategoryCart = localStorage.getItem('categorias_cart');
        if (oldCategoryCart && this.currentUser) {
            const cartKey = this.getUserCartKey('categorias');
            if (cartKey && !localStorage.getItem(cartKey)) {
                localStorage.setItem(cartKey, oldCategoryCart);
                localStorage.removeItem('categorias_cart');
                console.log('Carrito de categorías migrado exitosamente');
            }
        }

        this.updateCartCountDisplay();
    }

    // ========== INFORMACIÓN DE DEBUG ==========
    
    getDebugInfo() {
        return {
            currentUser: this.currentUser,
            productCartKey: this.getUserCartKey('productos'),
            categoryCartKey: this.getUserCartKey('categorias'),
            productCartItems: this.getProductCart().length,
            categoryCartItems: this.getCategoryCart().length
        };
    }
}

// Crear instancia global del gestor de carrito
window.cartManager = new CartManager();

// Funciones globales para compatibilidad con código existente
window.addToCart = function(product) {
    return window.cartManager.addProductToCart(product);
};

window.removeFromCart = function(codigo) {
    window.cartManager.removeProductFromCart(codigo);
};

window.clearCart = function() {
    if (confirm('¿Estás seguro de que quieres vaciar tu carrito?')) {
        window.cartManager.clearProductCart();
        if (typeof showCart === 'function') showCart();
    }
};

window.changeQuantity = function(codigo, change) {
    const cart = window.cartManager.getProductCart();
    const item = cart.find(item => item.codigo === codigo);
    if (item) {
        const newQuantity = item.cantidad + change;
        window.cartManager.updateProductQuantity(codigo, newQuantity);
        if (typeof showCart === 'function') showCart();
    }
};

// Funciones para categorías
window.addCategoryToCart = function(category) {
    return window.cartManager.addCategoryToCart(category);
};

window.removeCategoryFromCart = function(codigo) {
    window.cartManager.removeCategoryFromCart(codigo);
    if (typeof showCart === 'function') showCart();
};

// Función para migrar carritos existentes
window.migrateUserCarts = async function() {
    await window.cartManager.migrateOldCarts();
};

// Función para limpiar carritos al hacer logout
window.clearUserCarts = function() {
    window.cartManager.clearAllUserCarts();
};

console.log('🛒 Sistema de Carrito Individual cargado correctamente');