# ADR-003: Mock Settlement vs Real Payments

## Status
Accepted

## Context
The reference architecture needs to demonstrate settlement and payment processing patterns without the complexity of real payment integration. We must decide between implementing mock settlement versus integrating with real payment providers like Stripe.

## Decision
Implement **mock settlement with realistic escrow simulation** rather than real payment processing integration.

## Rationale

### Why Mock Settlement

#### 1. Focus on Architecture
The primary goal is demonstrating trust boundary architecture, not payment processing. Mock settlement allows focus on the architectural patterns without payment complexity.

#### 2. Reduced Complexity
Real payment integration introduces significant complexity:
- API key management
- PCI compliance considerations
- Error handling for payment failures
- Webhook processing
- Refund and dispute handling

#### 3. Faster Development
Mock settlement can be implemented quickly without external dependencies, API rate limits, or testing account setup.

#### 4. Educational Clarity
Mock implementation makes the settlement logic and state transitions more visible and understandable for learning purposes.

#### 5. Cost Efficiency
No payment processing fees or test account costs during development and demonstration.

#### 6. Environment Independence
No dependency on external services, making the system portable and always available for demos.

### Why Not Real Payments

#### 1. Scope Creep
Real payment integration would significantly expand scope beyond the reference architecture objectives.

#### 2. Compliance Burden
Real payments introduce regulatory and compliance requirements that distract from architectural learning.

#### 3. Testing Complexity
Testing with real payments requires careful test data management and can be slow and expensive.

#### 4. Security Risks
Even with test accounts, real payment APIs introduce security considerations that must be managed.

#### 5. Maintenance Overhead
Payment APIs change frequently, requiring ongoing maintenance and updates.

## Mock Settlement Design

### Core Components

#### 1. Escrow Service
Simulates holding funds during transaction lifecycle:

```python
class MockEscrow:
    def hold_funds(self, amount: float, payer: str, payee: str) -> str:
        """Hold funds in escrow, return transaction ID"""
        
    def release_funds(self, transaction_id: str) -> bool:
        """Release funds to payee"""
        
    def refund_funds(self, transaction_id: str, reason: str) -> bool:
        """Refund funds to payer"""
        
    def get_balance(self, account: str) -> float:
        """Get account balance"""
```

#### 2. Payment Processor
Simulates payment method validation and processing:

```python
class MockPaymentProcessor:
    def validate_payment_method(self, method: dict) -> bool:
        """Validate payment method (mock credit card, etc.)"""
        
    def process_payment(self, amount: float, method: dict) -> str:
        """Process payment, return authorization code"""
        
    def void_payment(self, auth_code: str) -> bool:
        """Void authorized payment"""
```

#### 3. Settlement Engine
Coordinates the complete settlement lifecycle:

```python
class MockSettlementEngine:
    def initiate_settlement(self, order: Order) -> str:
        """Start settlement process for an order"""
        
    def confirm_delivery(self, order_id: str) -> bool:
        """Confirm delivery and trigger fund release"""
        
    def handle_dispute(self, order_id: str, reason: str) -> bool:
        """Handle dispute resolution"""
```

### Realistic Simulation Features

#### 1. Account Balances
- Mock buyer accounts with starting balances
- Mock merchant accounts for receiving payments
- Balance tracking and validation

#### 2. Payment Methods
- Mock credit cards with validation
- Mock bank transfers
- Expiration date checking
- CVV validation simulation

#### 3. Transaction States
- `AUTHORIZED`: Payment approved, funds held
- `HELD`: Funds in escrow awaiting delivery
- `RELEASED`: Funds released to merchant
- `REFUNDED`: Funds returned to buyer
- `DISPUTED`: Under dispute resolution

#### 4. Timing Simulation
- Realistic processing delays
- Settlement windows (e.g., 3-day hold after delivery)
- Dispute resolution timelines

#### 5. Error Conditions
- Insufficient funds simulation
- Payment method declines
- Processing timeouts
- Network error simulation

### Integration Points

#### Merchant Integration
```python
# Merchant requests settlement
settlement_request = {
    "order_id": "ORDER123",
    "amount": 89.99,
    "merchant_account": "merchant_001",
    "payment_method": {
        "type": "credit_card",
        "last_four": "1234",
        "expiry": "12/25"
    }
}

# Settlement response
settlement_response = {
    "transaction_id": "TXN456",
    "status": "HELD",
    "release_date": "2024-01-20",
    "hold_amount": 89.99
}
```

#### Buyer Agent Integration
```python
# Agent checks settlement status
settlement_status = settlement_engine.get_status("TXN456")
# Returns: {"status": "HELD", "release_conditions": ["delivery_confirmed"]}
```

#### Approval Boundary Integration
```python
# Settlement waits for approval before processing
if approval_required:
    settlement_engine.wait_for_approval(order_id)
else:
    settlement_engine.process_immediately(order_id)
```

### Audit Trail Features

#### Transaction Logging
- All settlement events logged with timestamps
- State changes tracked with reasons
- Account balance updates recorded

#### Compliance Reporting
- Transaction volume reports
- Dispute resolution tracking
- Settlement timing analytics

## Boundary Definition

### Settlement Trust Boundary
1. **Fund Management**: Simulate holding and releasing funds
2. **Payment Validation**: Mock payment method verification
3. **State Coordination**: Manage settlement lifecycle states
4. **Dispute Resolution**: Handle payment disputes and refunds
5. **Audit Recording**: Log all settlement activities

### Boundary Interfaces
1. **Merchant Interface**: Receive settlement requests, provide status updates
2. **Buyer Interface**: Handle payment methods, provide transaction status
3. **Approval Interface**: Coordinate with approval workflows
4. **Audit Interface**: Record settlement events and state changes

### Boundary Validation Rules
1. **Sufficient Funds**: Verify buyer account has sufficient balance
2. **Valid Payment Method**: Mock payment method validation
3. **Release Conditions**: Verify conditions for fund release
4. **Dispute Validity**: Validate dispute claims and timing

## Realism Enhancements

### Data Generation
- Realistic account numbers and payment methods
- Plausible transaction amounts and timing
- Varied merchant and buyer profiles

### Behavioral Simulation
- Payment success/failure rates based on real data
- Processing time variations
- Dispute frequency patterns

### Monitoring Features
- Settlement dashboard showing transaction flow
- Account balance tracking
- Dispute resolution metrics

## Consequences

### Positive Consequences

#### 1. Architectural Clarity
Focus remains on trust boundaries and delegation patterns rather than payment processing details.

#### 2. Development Speed
No external dependencies or API integration complexity.

#### 3. Educational Value
Settlement logic is visible and understandable for learning.

#### 4. Demo Reliability
No external service dependencies that could fail during demonstrations.

#### 5. Cost Efficiency
No payment processing fees or infrastructure costs.

### Negative Consequences

#### 1. Limited Realism
Mock implementation doesn't demonstrate real payment challenges.

#### 2. Incomplete Learning
Developers don't learn about real payment integration patterns.

#### 3. Reduced Credibility
Some may view mock settlement as unrealistic.

#### 4. Extension Complexity
Future migration to real payments may require significant refactoring.

### Mitigation Strategies

#### 1. Realistic Mocking
Implement sophisticated simulation that mirrors real payment behavior.

#### 2. Documentation
Clearly document how mock patterns map to real payment integration.

#### 3. Extension Points
Design interfaces that can be easily replaced with real payment providers.

#### 4. Learning Resources
Provide references to real payment integration documentation.

## Implementation Phases

### Phase 1: Basic Mock Settlement
- Simple escrow simulation
- Basic payment method validation
- Transaction state management

### Phase 2: Enhanced Realism
- Account balance tracking
- Timing simulations
- Error condition handling

### Phase 3: Advanced Features
- Dispute resolution
- Compliance reporting
- Settlement analytics

## Future Migration Path

### Phase 4: Real Payment Integration
When moving to production:

#### 1. Interface Replacement
- Replace mock implementations with real payment providers
- Maintain existing boundary interfaces
- Add real payment error handling

#### 2. Security Enhancement
- Add PCI compliance measures
- Implement secure key management
- Add fraud detection

#### 3. Compliance Addition
- Add regulatory reporting
- Implement audit requirements
- Add dispute resolution procedures

#### 4. Monitoring Enhancement
- Add real payment monitoring
- Implement alerting for payment issues
- Add performance metrics

## Extension Points

### Payment Provider Abstraction
```python
class PaymentProvider(ABC):
    def process_payment(self, amount: float, method: dict) -> str:
        pass
    
    def refund_payment(self, transaction_id: str) -> bool:
        pass

class MockPaymentProvider(PaymentProvider):
    # Mock implementation

class StripePaymentProvider(PaymentProvider):
    # Real Stripe implementation
```

### Configuration-Driven Switching
```python
# Configuration
PAYMENT_PROVIDER = "mock"  # or "stripe"

# Factory pattern
provider = PaymentProviderFactory.create(PAYMENT_PROVIDER)
```

---

*This decision prioritizes architectural learning and development efficiency while maintaining the ability to migrate to real payment processing in production deployments.*
