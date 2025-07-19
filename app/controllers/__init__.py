from app.controllers.user import router as user_router
from app.controllers.mitra import router as mitra_router
from app.controllers.login import router as login_router
from app.controllers.order import router as order_router
from app.controllers.currency_price import router as currency_price_router
from app.controllers.mitra_coord import router as mitra_coord_router
from app.controllers.order_pickup import router as order_pickup_router
from app.controllers.order_assigned import router as order_assigned_router
from app.controllers.testingGraphhopper import router as testing_graphhopper_router
from app.controllers.testingOpenRouteService import router as testing_open_route_service_router
from app.controllers.autocomplete import router as autocomplete_service_router
from app.controllers.chat_mitra import router as chat_mitra_router
from app.controllers.redis_test import router as redis_test_router

def include_routers(app):
    app.include_router(
        login_router, prefix = "/api/v1", tags = ['login']
    )

    app.include_router(
        user_router, prefix ="/api/v1/users", tags = ['User']
    )
    
    app.include_router(
        mitra_router, prefix ="/api/v1/mitra", tags = ['Mitra']
    )

    app.include_router(
        order_router, prefix ="/api/v1/orders", tags = ['Order']
    )

    app.include_router(
        mitra_coord_router, prefix ="/api/v1/mitra_coord", tags = ['Mitra Coords']
    )

    app.include_router(
        order_pickup_router, prefix ="/api/v1/order_pickup", tags = ['Order Pickup']
    )

    app.include_router(
        order_assigned_router, prefix ="/api/v1/order_assigned", tags = ['Order Assigned']
    )

    app.include_router(
        autocomplete_service_router, prefix = "/api/v1/autocomplete", tags = ['autocomplete searching location']
    )

    app.include_router(
        currency_price_router, prefix ="/api/v1/currency_price", tags = ['Currency Price']
    )
    
    app.include_router(
        chat_mitra_router, prefix ="/api/v1/chat_mitra", tags = ['Chat Mitra']
    )
    
    app.include_router(
        redis_test_router, prefix ="/api/v1/redis_test", tags = ['Test Redis']
    )

    # app.include_router(
    #     testing_graphhopper_router, prefix ="/api/v1/testing_graphhopper", tags = ['Testing Graphhopper']
    # )
    # app.include_router(
    #     testing_open_route_service_router, prefix ="/api/v1/testing_open_route_service", tags = ['Testing Open Route Service']
    # )