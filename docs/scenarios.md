# Use Case Scenarios

## Primary Scenario: Laptop Bag Purchase

### Scenario Overview
**User Request**: "Buy a laptop bag under $120 with fast shipping"

### Step-by-Step Flow

#### 1. Intent Capture
**User Interface**: Streamlit web application
**Actions**:
- User specifies price constraint: <$120
- User selects shipping preference: "Fast shipping" (3-5 days)
- User confirms product category: "Laptop bag"
- System validates constraint completeness

**Boundary Crossing**: Human system interface
**Audit Event**: Intent captured with constraints {price_max: 120, shipping: fast, category: laptop_bag}

#### 2. Agent Search Initiation
**Component**: Buyer Agent
**Actions**:
- Agent receives validated intent
- Agent constructs search query for laptop bags
- Agent applies initial filters (price < $120, fast shipping available)

**Boundary Crossing**: Intent layer to agent decisioning
**Audit Event**: Agent search initiated with query parameters

#### 3. Catalog Query
**Component**: Merchant Catalog
**Actions**:
- Catalog receives search request from agent
- Catalog filters products by price and shipping availability
- Catalog returns 7 matching laptop bags

**Boundary Crossing**: Agent to merchant domain
**Audit Event**: Catalog query returned 7 results

#### 4. Product Evaluation
**Component**: Buyer Agent
**Actions**:
- Agent evaluates returned products against constraints
- Agent scores products on features (material, size, reviews)
- Agent identifies top 3 candidates
- Agent selects best option: "Professional Laptop Bag - $89, 4-day shipping"

**Boundary Crossing**: Agent decisioning within authority
**Audit Event**: Product selected: Professional Laptop Bag, $89, 4-day shipping

#### 5. Risk Assessment
**Component**: Buyer Agent
**Actions**:
- Agent evaluates purchase risk factors
- Risk factors: Price within range, reputable seller, standard checkout
- Risk score: Low (no approval required)
- Decision: Proceed to checkout

**Boundary Crossing**: Agent self-assessment
**Audit Event**: Risk assessment complete, score: LOW, approval not required

#### 6. Checkout Initiation
**Component**: Checkout API
**Actions**:
- API receives purchase request from agent
- API validates product availability (15 units in stock)
- API calculates total: $89 + $12 shipping = $101
- API creates order with pending status

**Boundary Crossing**: Agent to merchant checkout
**Audit Event**: Order created: #12345, total $101, status: PENDING_PAYMENT

#### 7. Payment Processing
**Component**: Settlement Module
**Actions**:
- Settlement receives payment request: $101
- Settlement validates payment method (mock credit card)
- Settlement places funds in escrow
- Settlement confirms payment held

**Boundary Crossing**: Merchant to settlement
**Audit Event**: Payment processed: $101 held in escrow, transaction #TXN001

#### 8. Order Confirmation
**Component**: Merchant Checkout
**Actions**:
- Checkout receives payment confirmation
- Checkout updates order status to CONFIRMED
- Checkout triggers fulfillment process
- Checkout sends confirmation to buyer agent

**Boundary Crossing**: Settlement to merchant
**Audit Event**: Order #12345 confirmed, fulfillment initiated

#### 9. Fulfillment Process
**Component**: Merchant Catalog
**Actions**:
- Catalog updates inventory (15 -> 14 units)
- Catalog generates shipping label
- Catalog schedules pickup (2-day processing)
- Catalog updates order status to SHIPPED

**Boundary Crossing**: Merchant internal process
**Audit Event**: Inventory updated, order #12345 shipped, tracking #TRK789

#### 10. Shipping Notification
**Component**: Buyer Agent
**Actions**:
- Agent receives shipping notification
- Agent tracks delivery progress
- Agent estimates delivery date (4 days from shipment)
- Agent prepares for delivery confirmation

**Boundary Crossing**: Merchant to agent
**Audit Event**: Shipping notification received, tracking #TRK789, ETA: 4 days

#### 11. Delivery Confirmation
**User Interface**: Streamlit web application
**Actions**:
- User receives delivery confirmation email
- User confirms product receipt via Streamlit
- System verifies delivery against tracking data
- System triggers settlement release

**Boundary Crossing**: Human system interface
**Audit Event**: Delivery confirmed by user, settlement release triggered

#### 12. Settlement Release
**Component**: Settlement Module
**Actions**:
- Settlement receives delivery confirmation
- Settlement validates release conditions (delivery confirmed, no disputes)
- Settlement releases funds to merchant account
- Settlement updates transaction status to COMPLETE

**Boundary Crossing**: Human confirmation to settlement
**Audit Event**: Settlement complete: $101 released to merchant, transaction #TXN001 closed

#### 13. Transaction Closure
**Component**: Audit System
**Actions**:
- Audit logs final transaction state
- Audit generates compliance report
- Audit verifies all boundaries properly crossed
- System archives transaction record

**Boundary Crossing**: System-wide audit
**Audit Event**: Transaction #12345 complete, all boundaries satisfied, audit verified

### Success Criteria
- All constraints satisfied (price < $120, fast shipping)
- All trust boundaries properly crossed with audit
- Human approval not required (low risk)
- Settlement completed successfully
- Complete audit trail maintained

### Total Duration
- **Search and Selection**: 2 minutes
- **Checkout and Payment**: 30 seconds
- **Processing and Shipping**: 4 days
- **Settlement**: Immediate after delivery
- **Total**: ~4 days

---

## Future Scenarios (Not Implemented)

### Scenario 2: High-Value Electronics Purchase

**User Request**: "Buy a professional laptop under $2000 with extended warranty"

**Key Differences from Primary Scenario**:
- **High Value**: Triggers mandatory human approval
- **Complex Constraints**: Extended warranty, professional specifications
- **Risk Assessment**: High risk score due to value
- **Approval Flow**: Requires explicit human approval before payment
- **Settlement**: Extended escrow period for high-value items

**New Boundary Crossings**:
- Approval boundary with human decision
- Extended settlement timeline
- Additional verification steps

### Scenario 3: Multi-Item Bundle Purchase

**User Request**: "Buy home office setup: desk, chair, and monitor under $800"

**Key Differences from Primary Scenario**:
- **Multi-Item**: Complex inventory coordination
- **Bundle Pricing**: Potential discounts and promotions
- **Partial Fulfillment**: Some items may be out of stock
- **Split Shipping**: Different delivery times for items
- **Complex Settlement**: Multiple merchant coordination

**New Boundary Crossings**:
- Multi-merchant settlement coordination
- Partial fulfillment handling
- Complex approval workflows

---

## Scenario Development Guidelines

### Constraint Complexity
- **Simple**: Single product, clear constraints (laptop bag scenario)
- **Medium**: Multiple products, moderate constraints (bundle scenario)
- **Complex**: High value, multiple constraints (electronics scenario)

### Risk Assessment Factors
- **Transaction Value**: Higher value = higher risk
- **Product Category**: Electronics higher risk than accessories
- **Seller Reputation**: New sellers trigger additional scrutiny
- **Payment Method**: Certain methods have different risk profiles

### Approval Triggers
- **Value Threshold**: Purchases over $500 require approval
- **Category Risk**: Electronics always require approval
- **New Sellers**: First-time purchases require approval
- **Unusual Patterns**: Deviations from normal behavior

### Settlement Variations
- **Standard**: Immediate release after delivery (accessories)
- **Extended**: 7-day hold after delivery (electronics)
- **Escalated**: Manual release for disputed items
- **Partial**: Proportional release for partial fulfillment

---

*These scenarios demonstrate how the trust boundary architecture handles various complexity levels while maintaining security and audit requirements.*
