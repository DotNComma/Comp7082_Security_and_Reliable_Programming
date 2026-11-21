import pytest
from cart import ShoppingCart
from checkout import CheckoutService
from payments import FakePaymentGateway
from repository import StoreRepository
from setup_db import initialize


@pytest.fixture
def repo(tmp_path):
    db_file = tmp_path / "test_shop.db"
    initialize(str(db_file))
    return StoreRepository(str(db_file))


def test_add_item_and_subtotal(repo):
    cart = ShoppingCart("u1", repo)
    assert cart.add_item("MOU-01", 2) is True
    assert cart.subtotal() == pytest.approx(59.90)
    assert cart.total() == pytest.approx(59.90)


def test_add_item_rejects_unknown_sku(repo):
    cart = ShoppingCart("u1", repo)
    assert cart.add_item("NOPE-99", 1) is False
    assert cart.lines == []


def test_add_item_respects_cumulative_stock(repo):
    cart = ShoppingCart("u1", repo)
    assert cart.add_item("LAP-01", 3) is True
    assert cart.add_item("LAP-01", 3) is False 
    assert cart.lines[0].quantity == 3


def test_add_item_rejects_non_positive_quantity(repo):
    cart = ShoppingCart("u1", repo)
    assert cart.add_item("USB-01", 0) is False
    assert cart.add_item("USB-01", -1) is False


def test_remove_item_partial_and_full(repo):
    cart = ShoppingCart("u1", repo)
    cart.add_item("USB-01", 4)
    assert cart.remove_item("USB-01", 1) is True
    assert cart.lines[0].quantity == 3
    assert cart.remove_item("USB-01") is True
    assert cart.lines == []


def test_discount_does_not_go_negative(repo):
    cart = ShoppingCart("u1", repo)
    cart.add_item("USB-01", 1)
    assert cart.apply_discount("SAVE15") is False
    assert cart.total() == pytest.approx(9.99)


def test_invalid_discount_rejected(repo):
    cart = ShoppingCart("u1", repo)
    cart.add_item("USB-01", 1)
    assert cart.apply_discount("FAKE50") is False
    assert cart.total() == pytest.approx(9.99)


def test_save_and_load_cart(repo):
    cart = ShoppingCart("u1", repo)
    cart.add_item("MOU-01", 2)
    cart.save()

    reloaded = ShoppingCart("u1", repo)
    reloaded.load()
    assert len(reloaded.lines) == 1
    assert reloaded.lines[0].sku == "MOU-01"
    assert reloaded.lines[0].quantity == 2


def test_sql_injection_safe_lookup(repo):
    payload = "' OR '1'='1"
    assert repo.get_product(payload) is None
    assert repo.get_saved_cart(payload) == []


def test_checkout_empty_cart(repo):
    gateway = FakePaymentGateway(should_approve=True)
    service = CheckoutService(repo, gateway)
    cart = ShoppingCart("u1", repo)

    result = service.checkout(cart, "tok_fake_123", "req-1")
    assert result.status == "empty"
    assert result.order_id is None
    assert gateway.calls == []


def test_checkout_approved_decrements_stock_and_clears_cart(repo):
    gateway = FakePaymentGateway(should_approve=True)
    service = CheckoutService(repo, gateway)
    cart = ShoppingCart("u1", repo)
    cart.add_item("LAP-01", 2)

    result = service.checkout(cart, "tok_fake_approved", "req-100")
    assert result.status == "paid"
    assert result.order_id is not None
    assert repo.get_product("LAP-01").stock == 3
    assert cart.lines == []
    assert gateway.calls == [(pytest.approx(1999.98), "tok_fake_approved")]


def test_checkout_declined_preserves_stock_and_cart(repo):
    gateway = FakePaymentGateway(should_approve=False)
    service = CheckoutService(repo, gateway)
    cart = ShoppingCart("u1", repo)
    cart.add_item("LAP-01", 2)

    result = service.checkout(cart, "tok_fake_declined", "req-101")
    assert result.status == "declined"
    assert repo.get_product("LAP-01").stock == 5
    assert len(cart.lines) == 1