(() => {
  const $ = (id) => document.getElementById(id);
  const status = (id, msg, type = "info") => {
    const el = $(id);
    if (!el) return;
    el.textContent = msg;
    el.className = `status ${type}`;
    setTimeout(() => (el.textContent = ""), 3000);
  };

  // Load/save API base URLs
  const loadConfig = () => {
    const cfg = JSON.parse(localStorage.getItem("apiConfig") || "{}");
    if (cfg.product) $("product-api").value = cfg.product;
    if (cfg.auth) $("auth-api").value = cfg.auth;
    if (cfg.order) $("order-api").value = cfg.order;
  };
  const saveConfig = () => {
    const cfg = {
      product: $("product-api").value.trim(),
      auth: $("auth-api").value.trim(),
      order: $("order-api").value.trim(),
    };
    localStorage.setItem("apiConfig", JSON.stringify(cfg));
    status("config-status", "Saved", "success");
  };

  let token = "";
  const setToken = (t) => {
    token = t || "";
    $("jwt-token").value = token;
  };

  const headers = (withAuth = false) => {
    const h = { "Content-Type": "application/json" };
    if (withAuth && token) h["Authorization"] = `Bearer ${token}`;
    return h;
  };

  const api = {
    product: () => $("product-api").value.trim(),
    auth: () => $("auth-api").value.trim(),
    order: () => $("order-api").value.trim(),
  };

  // Auth
  $("btn-register").onclick = async () => {
    const body = {
      username: $("auth-username").value,
      email: $("auth-email").value,
      password: $("auth-password").value,
    };
    const role = $("auth-role").value.trim();
    if (role) body.role = role;
    const res = await fetch(`${api.auth()}/register`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    $("auth-output").textContent = JSON.stringify(data, null, 2);
    if (res.ok && data.token) setToken(data.token);
  };

  $("btn-login").onclick = async () => {
    const body = {
      username: $("auth-username").value,
      password: $("auth-password").value,
    };
    const res = await fetch(`${api.auth()}/login`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    $("auth-output").textContent = JSON.stringify(data, null, 2);
    if (res.ok && data.token) setToken(data.token);
  };

  // Products
  $("btn-create-product").onclick = async () => {
    const body = {
      name: $("prod-name").value,
      price: parseFloat($("prod-price").value),
      stock_quantity: parseInt($("prod-stock").value || "0", 10),
      category: $("prod-category").value || "general",
      discount_percentage: parseFloat($("prod-discount").value || "0"),
      image_url: $("prod-image").value || null,
    };
    const res = await fetch(`${api.product()}/products`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    $("products-output").textContent = JSON.stringify(data, null, 2);
  };

  $("btn-list-products").onclick = async () => {
    const params = new URLSearchParams();
    const search = $("prod-search").value.trim();
    const cat = $("prod-filter-category").value.trim();
    params.set("page", $("prod-page").value || 1);
    params.set("per_page", $("prod-per-page").value || 5);
    params.set("sort_by", $("prod-sort-by").value);
    params.set("sort_order", $("prod-sort-order").value);
    if (search) params.set("search", search);
    if (cat) params.set("category", cat);
    const res = await fetch(`${api.product()}/products?${params.toString()}`);
    const data = await res.json().catch(() => ({}));
    $("products-output").textContent = JSON.stringify(data, null, 2);
  };

  // Orders
  $("btn-create-order").onclick = async () => {
    const useToken = $("order-use-token").checked;
    const hasToken = useToken && !!token;
    const body = {
      items: [
        {
          product_id: parseInt($("order-product-id").value || "1", 10),
          quantity: parseInt($("order-qty").value || "1", 10),
        },
      ],
      shipping_address: $("order-address").value || "123 Main St",
    };

    // Always include user_id if provided (helps v1). For v2, token is used.
    const userIdInput = $("order-user-id").value;
    if (userIdInput) {
      body.user_id = parseInt(userIdInput, 10);
    } else if (!hasToken) {
      $("orders-output").textContent = "For v1 without login, provide user_id (or log in and use token).";
      return;
    }

    const res = await fetch(`${api.order()}/orders`, {
      method: "POST",
      headers: headers(hasToken),
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    $("orders-output").textContent = JSON.stringify(data, null, 2);
  };

  $("save-config").onclick = saveConfig;

  loadConfig();
})();

