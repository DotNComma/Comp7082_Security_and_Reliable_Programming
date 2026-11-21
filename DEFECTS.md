# 8 Defects and Fixes
1. ShoppingCart.addItem, added a check for quantity when adding an item
    - This ensures that the quantity being asked for is not 0 or less
2. ShoppingCart.addItem, changed the logic for checking if there is enough stock for the quantity asked
    - Changed it to check for current quantity in the cart + added amount
    - This ensures that the quantity added up together does not exceed the current product stock
3. ShoppingCart.applyDiscount, changed the logic for checking coupon SAVE15
    - Changed it to check that the SAVE15 does not discount costs below $15
    - Made it so the discount does not work if the cost amount is below $15
    - This ensures that the cost of the current cart cannot go below $0 
4. CheckoutService.checkout, refactored large order, missing id check for better readability
    - Made it easier to read by combining the needed if statements into one
5. CheckoutService.checkout, moved updating stock after payment
    - This ensures that the product does remove a stock if a payment gets declined
6. CheckoutService.checkout, put cart clearing code in check for successful payments
    - This ensures that failed payments do not clear up the cart
7. StoreRespository, changed all the direct coded sql, to use parameterized queries
    - This ensure that the sql calls are protected from sql injections
8. StoreRespository.update_stock, added a check on quantity
    - This ensure that the quantity cannot be negative, so the computation won't go backwards

# Test Results
All test passed, seen in the photo posted Test Results.png