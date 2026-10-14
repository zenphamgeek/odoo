/**
 * ==============================================================================
 * 4-Vector Adversarial Scenario Test Suite Directive for HOOT Test Harness
 * ==============================================================================
 * Platform: Insilos Enterprise Platform / Odoo 20 LTS Hard Fork
 * Target: High-Throughput HOOT Harness & Domain Integrity Engine
 *
 * Vectors:
 *  Vector 1: State Machine Invariant Proof (S x E -> S', illegal transition proof)
 *  Vector 2: Concurrency Race Interleaving & Optimistic Locking (20 parallel workers, zero lost updates)
 *  Vector 3: Boundary Value Stress & Poison Pills (0, -1, 2^63-1, NaN/Inf, circular, 1MB payload)
 *  Vector 4: Partial Failure & Clean Rollback & Multi-Tenant Isolation (0 orphans, company_id isolation)
 * ==============================================================================
 */

const assert = require('assert');
const crypto = require('crypto');

// ==============================================================================
// CUSTOM DOMAIN ERRORS
// ==============================================================================

class DomainStateError extends Error {
  constructor(message, { fromState, event, allowedEvents } = {}) {
    super(message);
    this.name = 'DomainStateError';
    this.fromState = fromState;
    this.event = event;
    this.allowedEvents = allowedEvents;
  }
}

class OptimisticLockError extends Error {
  constructor(message, { recordId, expectedVersion, actualVersion } = {}) {
    super(message);
    this.name = 'OptimisticLockError';
    this.recordId = recordId;
    this.expectedVersion = expectedVersion;
    this.actualVersion = actualVersion;
  }
}

class PoisonPillValidationError extends Error {
  constructor(message, { field, value, reason } = {}) {
    super(message);
    this.name = 'PoisonPillValidationError';
    this.field = field;
    this.value = value;
    this.reason = reason;
  }
}

class AtomicPipelineRollbackError extends Error {
  constructor(message, { failedStep, originalError, compensationsExecuted } = {}) {
    super(message);
    this.name = 'AtomicPipelineRollbackError';
    this.failedStep = failedStep;
    this.originalError = originalError;
    this.compensationsExecuted = compensationsExecuted;
  }
}

class TenantBoundaryViolationError extends Error {
  constructor(message, { expectedCompanyId, attemptedCompanyId, recordId } = {}) {
    super(message);
    this.name = 'TenantBoundaryViolationError';
    this.expectedCompanyId = expectedCompanyId;
    this.attemptedCompanyId = attemptedCompanyId;
    this.recordId = recordId;
  }
}

// ==============================================================================
// VECTOR 1 IMPLEMENTATION: STATE MACHINE INVARIANT PROOF (S x E -> S')
// ==============================================================================

const States = Object.freeze({
  DRAFT: 'draft',
  CONFIRMED: 'confirmed',
  PROCESSED: 'processed',
  DONE: 'done',
  CANCELLED: 'cancelled',
});

const Events = Object.freeze({
  CONFIRM: 'confirm',
  PROCESS: 'process',
  COMPLETE: 'complete',
  CANCEL: 'cancel',
});

/**
 * Formal Transition Table: S x E -> S'
 */
const TRANSITION_TABLE = Object.freeze({
  [States.DRAFT]: Object.freeze({
    [Events.CONFIRM]: States.CONFIRMED,
    [Events.CANCEL]: States.CANCELLED,
  }),
  [States.CONFIRMED]: Object.freeze({
    [Events.PROCESS]: States.PROCESSED,
    [Events.CANCEL]: States.CANCELLED,
  }),
  [States.PROCESSED]: Object.freeze({
    [Events.COMPLETE]: States.DONE,
  }),
  [States.DONE]: Object.freeze({}),
  [States.CANCELLED]: Object.freeze({}),
});

class DocumentStateMachine {
  constructor(id, initialState = States.DRAFT) {
    this.id = id;
    this.state = initialState;
    this.history = [{ state: initialState, event: null, timestamp: Date.now() }];
  }

  transition(event) {
    const validMap = TRANSITION_TABLE[this.state] || {};
    const nextState = validMap[event];

    if (!nextState) {
      const allowed = Object.keys(validMap);
      throw new DomainStateError(
        `Illegal transition: Cannot apply event '${event}' to state '${this.state}'. Allowed events: [${allowed.join(', ')}]`,
        { fromState: this.state, event, allowedEvents: allowed }
      );
    }

    const prevState = this.state;
    this.state = nextState;
    this.history.push({ state: nextState, event, timestamp: Date.now(), fromState: prevState });
    return this.state;
  }
}

async function testVector1StateMachineInvariants() {
  console.log('\n🔵 [Vector 1] State Machine Invariant Proof (S x E -> S\')');
  let assertions = 0;

  // 1. Nominal Path: Draft -> Confirmed -> Processed -> Done
  const doc = new DocumentStateMachine('doc-001', States.DRAFT);
  assert.strictEqual(doc.state, States.DRAFT);
  assertions++;

  doc.transition(Events.CONFIRM);
  assert.strictEqual(doc.state, States.CONFIRMED);
  assertions++;

  doc.transition(Events.PROCESS);
  assert.strictEqual(doc.state, States.PROCESSED);
  assertions++;

  doc.transition(Events.COMPLETE);
  assert.strictEqual(doc.state, States.DONE);
  assertions++;

  // 2. Cancellation Branches
  const docCancel1 = new DocumentStateMachine('doc-cancel-1', States.DRAFT);
  docCancel1.transition(Events.CANCEL);
  assert.strictEqual(docCancel1.state, States.CANCELLED);
  assertions++;

  const docCancel2 = new DocumentStateMachine('doc-cancel-2', States.CONFIRMED);
  docCancel2.transition(Events.CANCEL);
  assert.strictEqual(docCancel2.state, States.CANCELLED);
  assertions++;

  // 3. Exhaustive Cartesian Product Proof (5 states x 4 events = 20 pairs)
  const allStates = Object.values(States);
  const allEvents = Object.values(Events);
  let illegalCount = 0;
  let legalCount = 0;

  for (const s of allStates) {
    for (const e of allEvents) {
      const isLegal = TRANSITION_TABLE[s] && TRANSITION_TABLE[s][e] !== undefined;
      const testDoc = new DocumentStateMachine(`doc-matrix-${s}-${e}`, s);

      if (isLegal) {
        const target = TRANSITION_TABLE[s][e];
        const res = testDoc.transition(e);
        assert.strictEqual(res, target, `State mismatch on legal transition: ${s} + ${e} -> ${target}`);
        legalCount++;
        assertions++;
      } else {
        assert.throws(
          () => testDoc.transition(e),
          (err) => {
            assert(err instanceof DomainStateError, `Error must be DomainStateError, got: ${err}`);
            assert.strictEqual(err.fromState, s, `fromState mismatch in error`);
            assert.strictEqual(err.event, e, `event mismatch in error`);
            return true;
          },
          `Expected DomainStateError for illegal transition (${s} + ${e})`
        );
        illegalCount++;
        assertions++;
      }
    }
  }

  // 4. Specific Directive Invariant: Cancelled -> Processed MUST throw DomainStateError
  const cancelledDoc = new DocumentStateMachine('doc-cancelled-inv', States.CANCELLED);
  assert.throws(
    () => cancelledDoc.transition(Events.PROCESS),
    DomainStateError,
    'Cancelled -> Processed must throw DomainStateError'
  );
  assertions++;

  // Done -> Draft / Confirm / Process / Cancel must throw DomainStateError
  const doneDoc = new DocumentStateMachine('doc-done-inv', States.DONE);
  for (const e of allEvents) {
    assert.throws(() => doneDoc.transition(e), DomainStateError);
    assertions++;
  }

  console.log(`  ✓ Verified nominal lifecycle: DRAFT -> CONFIRMED -> PROCESSED -> DONE`);
  console.log(`  ✓ Verified cancellation branches from DRAFT and CONFIRMED`);
  console.log(`  ✓ Cartesian transition matrix proof: ${legalCount} legal, ${illegalCount} illegal transitions verified`);
  console.log(`  ✓ Verified Cancelled -> Processed and Done -> * illegal transition guarantees`);
  console.log(`  [Pass: Vector 1 with ${assertions} verified assertions]`);
  return { vector: 1, passed: true, assertions };
}

// ==============================================================================
// VECTOR 2 IMPLEMENTATION: CONCURRENCY RACE INTERLEAVING & OPTIMISTIC LOCKING
// ==============================================================================

class OptimisticRecordStore {
  constructor() {
    this.records = new Map();
    this.writeSeq = 0n;
  }

  initRecord(id, initialData) {
    const record = {
      id,
      version: 1,
      writeTimestamp: Date.now(),
      seq: ++this.writeSeq,
      data: { ...initialData },
      history: [{ version: 1, data: { ...initialData }, timestamp: Date.now(), seq: this.writeSeq }],
    };
    this.records.set(id, record);
    return { ...record };
  }

  get(id) {
    const r = this.records.get(id);
    if (!r) return null;
    return {
      id: r.id,
      version: r.version,
      writeTimestamp: r.writeTimestamp,
      seq: r.seq,
      data: { ...r.data },
    };
  }

  async update(id, expectedVersion, mutatorFn, workerId) {
    // Inject asynchronous interleaving jitter (0 - 5ms) to simulate real network/DB race
    await new Promise((resolve) => setTimeout(resolve, Math.floor(Math.random() * 5)));

    const current = this.records.get(id);
    if (!current) {
      throw new Error(`Record ${id} not found`);
    }

    // Atomic CAS check
    if (current.version !== expectedVersion) {
      throw new OptimisticLockError(
        `Optimistic lock conflict on record ${id}: expected version ${expectedVersion}, actual version ${current.version}`,
        { recordId: id, expectedVersion, actualVersion: current.version }
      );
    }

    const nextData = mutatorFn({ ...current.data });
    const now = Date.now();
    current.version += 1;
    current.writeTimestamp = Math.max(now, current.writeTimestamp);
    current.seq = ++this.writeSeq;
    current.data = nextData;
    current.history.push({
      version: current.version,
      workerId,
      data: nextData,
      timestamp: current.writeTimestamp,
      seq: current.seq,
    });

    return {
      id: current.id,
      version: current.version,
      writeTimestamp: current.writeTimestamp,
      seq: current.seq,
      data: { ...current.data },
    };
  }
}

async function testVector2ConcurrencyRaceInvariants() {
  console.log('\n🔵 [Vector 2] Concurrency Race Interleaving & Optimistic Locking');
  let assertions = 0;
  const store = new OptimisticRecordStore();
  const testId = 'race-record-001';

  // 1. Single Version Race: 20 workers race simultaneously for Version 1 -> Version 2
  store.initRecord(testId, { counter: 0 });
  const initialSnap = store.get(testId);
  assert.strictEqual(initialSnap.version, 1);
  assertions++;

  const WORKER_COUNT = 20;
  const raceResults = await Promise.allSettled(
    Array.from({ length: WORKER_COUNT }, (_, i) =>
      store.update(testId, 1, (d) => ({ counter: d.counter + 1 }), `worker-${i + 1}`)
    )
  );

  const winners = raceResults.filter((r) => r.status === 'fulfilled');
  const losers = raceResults.filter((r) => r.status === 'rejected');

  assert.strictEqual(winners.length, 1, `Exactly 1 winner must win Version 1 -> 2 race; got ${winners.length}`);
  assertions++;
  assert.strictEqual(losers.length, WORKER_COUNT - 1, `Exactly 19 workers must lose and receive lock error; got ${losers.length}`);
  assertions++;

  // Verify all 19 losers received OptimisticLockError
  for (const loser of losers) {
    assert(loser.reason instanceof OptimisticLockError, `Loser error must be OptimisticLockError, got: ${loser.reason}`);
    assert.strictEqual(loser.reason.expectedVersion, 1);
    assert.strictEqual(loser.reason.actualVersion, 2);
    assertions++;
  }

  const postRaceSnap = store.get(testId);
  assert.strictEqual(postRaceSnap.version, 2, 'Version must be incremented exactly once');
  assert.strictEqual(postRaceSnap.data.counter, 1, 'Counter must be incremented exactly once');
  assertions += 2;

  // 2. Interleaved Parallel Updates with Retries: 20 workers concurrently increment counter (Zero Lost Updates)
  const retryRecordId = 'race-retry-002';
  store.initRecord(retryRecordId, { counter: 0, contributors: [] });

  async function workerWithRetry(workerId) {
    let attempts = 0;
    const maxAttempts = 100;
    while (attempts < maxAttempts) {
      attempts++;
      const current = store.get(retryRecordId);
      try {
        await store.update(
          retryRecordId,
          current.version,
          (d) => ({
            counter: d.counter + 1,
            contributors: [...d.contributors, workerId],
          }),
          workerId
        );
        return { workerId, attempts };
      } catch (err) {
        if (err instanceof OptimisticLockError) {
          // Exponential backoff with random jitter
          const backoff = Math.min(20, Math.pow(1.5, attempts)) + Math.random() * 5;
          await new Promise((r) => setTimeout(r, backoff));
          continue;
        }
        throw err;
      }
    }
    throw new Error(`Worker ${workerId} exhausted ${maxAttempts} retry attempts`);
  }

  const retryWorkers = Array.from({ length: WORKER_COUNT }, (_, i) => workerWithRetry(`retry-worker-${i + 1}`));
  const retryResults = await Promise.all(retryWorkers);

  assert.strictEqual(retryResults.length, WORKER_COUNT, 'All 20 workers must eventually succeed');
  assertions++;

  const finalRecord = store.get(retryRecordId);
  assert.strictEqual(finalRecord.version, 1 + WORKER_COUNT, `Final version must be exactly initial (1) + ${WORKER_COUNT} = ${1 + WORKER_COUNT}`);
  assertions++;
  assert.strictEqual(finalRecord.data.counter, WORKER_COUNT, `Final counter must equal ${WORKER_COUNT} (Zero Lost Updates)`);
  assertions++;
  assert.strictEqual(finalRecord.data.contributors.length, WORKER_COUNT, 'All worker contributions must be preserved');
  assertions++;

  // Verify write sequence numbers and write timestamps strictly monotonic
  const rawRecord = store.records.get(retryRecordId);
  for (let i = 1; i < rawRecord.history.length; i++) {
    const prev = rawRecord.history[i - 1];
    const curr = rawRecord.history[i];
    assert.strictEqual(curr.version, prev.version + 1, 'Versions in history must be strictly sequential');
    assert(curr.seq > prev.seq, 'Write sequence numbers must be strictly increasing');
    assert(curr.timestamp >= prev.timestamp, 'Write timestamps must be non-decreasing');
    assertions += 3;
  }

  console.log(`  ✓ Single-version race: 20 simultaneous workers -> exactly 1 winner, 19 OptimisticLockError`);
  console.log(`  ✓ Concurrent retry interleaving: 20 parallel workers serialized without lost updates`);
  console.log(`  ✓ Strict monotonicity verified for versions (1 -> 21) and write timestamps`);
  console.log(`  [Pass: Vector 2 with ${assertions} verified assertions]`);
  return { vector: 2, passed: true, assertions };
}

// ==============================================================================
// VECTOR 3 IMPLEMENTATION: BOUNDARY VALUE STRESS & POISON PILLS
// ==============================================================================

class SafePayloadHandler {
  static normalizeAndValidate(input, options = {}) {
    const maxStringBytes = options.maxStringBytes || 5 * 1024 * 1024; // 5MB guard
    const seenObjects = new WeakSet();

    function walk(val, path = 'root') {
      // 1. Primitive null / undefined
      if (val === null || val === undefined) {
        return val;
      }

      // 2. BigInt Boundary Check (2^63 - 1)
      if (typeof val === 'bigint') {
        const MAX_INT64 = 9223372036854775807n;
        const MIN_INT64 = -9223372036854775808n;
        if (val > MAX_INT64 || val < MIN_INT64) {
          throw new PoisonPillValidationError(`BigInt exceeds 64-bit bounds: ${val.toString()}`, {
            field: path,
            value: val.toString(),
            reason: 'INT64_OVERFLOW',
          });
        }
        return `__BIGINT__:${val.toString()}`;
      }

      // 3. Number Boundary Checks (NaN, +Inf, -Inf, 0, -1)
      if (typeof val === 'number') {
        if (Number.isNaN(val)) {
          return '__FLOAT_NAN__';
        }
        if (!Number.isFinite(val)) {
          return val > 0 ? '__FLOAT_POS_INF__' : '__FLOAT_NEG_INF__';
        }
        return val;
      }

      // 4. Large String Chunk Boundary (e.g. 1MB chunk)
      if (typeof val === 'string') {
        const byteLen = Buffer.byteLength(val, 'utf8');
        if (byteLen > maxStringBytes) {
          throw new PoisonPillValidationError(`String byte size ${byteLen} exceeds limit ${maxStringBytes}`, {
            field: path,
            value: `String(len=${byteLen})`,
            reason: 'STRING_SIZE_EXCEEDED',
          });
        }
        return val;
      }

      // 5. Booleans and symbols
      if (typeof val !== 'object') {
        return val;
      }

      // 6. Circular Reference Detection
      if (seenObjects.has(val)) {
        return '__CIRCULAR_REF__';
      }
      seenObjects.add(val);

      // 7. Arrays (including empty arrays [])
      if (Array.isArray(val)) {
        return val.map((item, idx) => walk(item, `${path}[${idx}]`));
      }

      // 8. Objects (handling null keys, odd structures)
      const sanitizedObj = {};
      const keys = Object.keys(val);
      for (const k of keys) {
        sanitizedObj[k] = walk(val[k], `${path}.${k}`);
      }
      return sanitizedObj;
    }

    return walk(input);
  }

  static safeSerialize(input) {
    const normalized = SafePayloadHandler.normalizeAndValidate(input);
    return JSON.stringify(normalized);
  }
}

async function testVector3BoundaryValueStress() {
  console.log('\n🔵 [Vector 3] Boundary Value Stress & Poison Pills');
  let assertions = 0;

  // 1. Boundary: 0 and -1
  const zeroTest = SafePayloadHandler.normalizeAndValidate({ valZero: 0, valNegativeOne: -1 });
  assert.strictEqual(zeroTest.valZero, 0);
  assert.strictEqual(zeroTest.valNegativeOne, -1);
  assertions += 2;

  // 2. Boundary: 2^63 - 1 BigInt (9223372036854775807n)
  const maxInt64 = 9223372036854775807n;
  const bigIntResult = SafePayloadHandler.normalizeAndValidate({ maxInt: maxInt64 });
  assert.strictEqual(bigIntResult.maxInt, '__BIGINT__:9223372036854775807');
  assertions++;

  // BigInt Overflow (> 2^63 - 1) must be intercepted cleanly
  const overflowInt = 9223372036854775808n;
  assert.throws(
    () => SafePayloadHandler.normalizeAndValidate({ overflow: overflowInt }),
    (err) => err instanceof PoisonPillValidationError && err.reason === 'INT64_OVERFLOW'
  );
  assertions++;

  // 3. Float NaN and Infs
  const floatPill = {
    nanVal: NaN,
    posInf: Infinity,
    negInf: -Infinity,
  };
  const floatResult = SafePayloadHandler.normalizeAndValidate(floatPill);
  assert.strictEqual(floatResult.nanVal, '__FLOAT_NAN__');
  assert.strictEqual(floatResult.posInf, '__FLOAT_POS_INF__');
  assert.strictEqual(floatResult.negInf, '__FLOAT_NEG_INF__');
  assertions += 3;

  // 4. Empty Arrays and Deeply Nested Empty Structures
  const emptyPill = {
    emptyArr: [],
    nestedEmptyArr: [[], [[]]],
    emptyObj: {},
    deepObj: { a: { b: {} } },
  };
  const emptyResult = SafePayloadHandler.normalizeAndValidate(emptyPill);
  assert.deepStrictEqual(emptyResult.emptyArr, []);
  assert.deepStrictEqual(emptyResult.nestedEmptyArr, [[], [[]]]);
  assert.deepStrictEqual(emptyResult.emptyObj, {});
  assertions += 3;

  // 5. Null Keys and Values
  const nullPill = {
    [null]: null,
    undefinedKey: undefined,
    nullVal: null,
    emptyKey: '',
  };
  const nullResult = SafePayloadHandler.normalizeAndValidate(nullPill);
  assert.strictEqual(nullResult['null'], null);
  assert.strictEqual(nullResult.undefinedKey, undefined);
  assert.strictEqual(nullResult.nullVal, null);
  assertions += 3;

  // 6. Circular Reference Structures
  const circularObj = { id: 'poison-circ-001', name: 'cyclic' };
  circularObj.self = circularObj;
  circularObj.nested = { parent: circularObj };

  // Must not throw RangeError (Maximum call stack size exceeded)
  let serializedCircular = null;
  assert.doesNotThrow(() => {
    serializedCircular = SafePayloadHandler.safeSerialize(circularObj);
  });
  assert(serializedCircular !== null);
  assert(serializedCircular.includes('__CIRCULAR_REF__'), 'Circular reference must be normalized to marker');
  assertions += 2;

  // 7. 1MB String Chunk Stress Test
  const oneMbChunk = 'A'.repeat(1024 * 1024);
  const t0 = Date.now();
  const chunkResult = SafePayloadHandler.normalizeAndValidate({ payload: oneMbChunk });
  const tDuration = Date.now() - t0;

  assert.strictEqual(chunkResult.payload.length, 1024 * 1024);
  assert(tDuration < 200, `1MB chunk processed under 200ms; took ${tDuration}ms`);
  assertions += 2;

  // Verify safe JSON serialization of the 1MB payload
  const hashPre = crypto.createHash('sha256').update(oneMbChunk).digest('hex');
  const hashPost = crypto.createHash('sha256').update(chunkResult.payload).digest('hex');
  assert.strictEqual(hashPre, hashPost, '1MB chunk data fidelity preserved without bit corruption');
  assertions++;

  // 8. OOM Poison Pill Guard (> 5MB String)
  const sixMbString = 'B'.repeat(6 * 1024 * 1024);
  assert.throws(
    () => SafePayloadHandler.normalizeAndValidate({ oversized: sixMbString }),
    (err) => err instanceof PoisonPillValidationError && err.reason === 'STRING_SIZE_EXCEEDED'
  );
  assertions++;

  console.log(`  ✓ Numeric boundaries verified: 0, -1, 2^63-1 BigInt, INT64_OVERFLOW`);
  console.log(`  ✓ Float anomalies sanitized: NaN, +Infinity, -Infinity`);
  console.log(`  ✓ Structure edge cases: empty arrays, nested empties, null keys`);
  console.log(`  ✓ Circular reference graph safely unrolled without stack overflow`);
  console.log(`  ✓ 1MB payload ingested in ${tDuration}ms with SHA-256 bit integrity preserved`);
  console.log(`  [Pass: Vector 3 with ${assertions} verified assertions]`);
  return { vector: 3, passed: true, assertions };
}

// ==============================================================================
// VECTOR 4 IMPLEMENTATION: PARTIAL FAILURE, CLEAN ROLLBACK & MULTI-TENANT ISOLATION
// ==============================================================================

class MultiTenantStore {
  constructor() {
    this.records = new Map();
  }

  insert(record, tenantContext) {
    if (!tenantContext || !tenantContext.companyId) {
      throw new TenantBoundaryViolationError('Missing tenant context in write operation', {});
    }
    if (record.companyId && record.companyId !== tenantContext.companyId) {
      throw new TenantBoundaryViolationError(
        `Cross-tenant injection rejected: attempted to insert record with companyId ${record.companyId} under context companyId ${tenantContext.companyId}`,
        { expectedCompanyId: tenantContext.companyId, attemptedCompanyId: record.companyId, recordId: record.id }
      );
    }
    const fullRecord = { ...record, companyId: tenantContext.companyId };
    this.records.set(record.id, fullRecord);
    return { ...fullRecord };
  }

  get(id, tenantContext) {
    const rec = this.records.get(id);
    if (!rec) return null;
    if (rec.companyId !== tenantContext.companyId) {
      throw new TenantBoundaryViolationError(
        `Unauthorized cross-tenant read: Tenant ${tenantContext.companyId} attempted to read record ${id} owned by Tenant ${rec.companyId}`,
        { expectedCompanyId: rec.companyId, attemptedCompanyId: tenantContext.companyId, recordId: id }
      );
    }
    return { ...rec };
  }

  delete(id, tenantContext) {
    const rec = this.records.get(id);
    if (!rec) return false;
    if (rec.companyId !== tenantContext.companyId) {
      throw new TenantBoundaryViolationError(
        `Unauthorized cross-tenant delete: Tenant ${tenantContext.companyId} attempted to delete record ${id} owned by Tenant ${rec.companyId}`,
        { expectedCompanyId: rec.companyId, attemptedCompanyId: tenantContext.companyId, recordId: id }
      );
    }
    this.records.delete(id);
    return true;
  }

  query(tenantContext) {
    const out = [];
    for (const rec of this.records.values()) {
      if (rec.companyId === tenantContext.companyId) {
        out.push({ ...rec });
      }
    }
    return out;
  }

  size() {
    return this.records.size;
  }
}

class AtomicPipelineCoordinator {
  constructor(store) {
    this.store = store;
  }

  async execute3StepPipeline({ id, failAtStep = null, tenantContext }) {
    const compensations = [];
    let currentStep = 0;

    try {
      // ----------------------------------------------------
      // STEP 1: Resource Reservation / Draft Record
      // ----------------------------------------------------
      currentStep = 1;
      if (failAtStep === 1) {
        throw new Error('Fault injected at Step 1');
      }
      this.store.insert({ id, stage: 'reserved', amount: 100 }, tenantContext);
      compensations.push(async () => {
        this.store.delete(id, tenantContext);
      });

      // ----------------------------------------------------
      // STEP 2: Balance Transfer / Ledger Post
      // ----------------------------------------------------
      currentStep = 2;
      if (failAtStep === 2) {
        throw new Error('Fault injected at Step 2 (e.g. Insufficient Balance / Ledger Rejection)');
      }
      // Mutate to stage 2
      const step1Rec = this.store.get(id, tenantContext);
      this.store.insert({ ...step1Rec, stage: 'ledger_posted' }, tenantContext);

      // ----------------------------------------------------
      // STEP 3: Finalize / Release
      // ----------------------------------------------------
      currentStep = 3;
      if (failAtStep === 3) {
        throw new Error('Fault injected at Step 3 (e.g. Upstream Notification Timeout)');
      }
      const step2Rec = this.store.get(id, tenantContext);
      const finalized = this.store.insert({ ...step2Rec, stage: 'done' }, tenantContext);

      return finalized;
    } catch (err) {
      // Execute compensating rollbacks in reverse order (LIFO)
      const rollbackErrors = [];
      let executedRollbacks = 0;

      while (compensations.length > 0) {
        const comp = compensations.pop();
        try {
          await comp();
          executedRollbacks++;
        } catch (cErr) {
          rollbackErrors.push(cErr);
        }
      }

      throw new AtomicPipelineRollbackError(
        `Pipeline failed at Step ${currentStep}; ${executedRollbacks} compensations applied. Original error: ${err.message}`,
        {
          failedStep: currentStep,
          originalError: err,
          compensationsExecuted: executedRollbacks,
        }
      );
    }
  }
}

async function testVector4PartialFailureAndTenancy() {
  console.log('\n🔵 [Vector 4] Partial Failure, Clean Rollback & Multi-Tenant Isolation');
  let assertions = 0;
  const store = new MultiTenantStore();
  const coordinator = new AtomicPipelineCoordinator(store);

  const tenantA = { companyId: 101, name: 'Tenant Alpha' };
  const tenantB = { companyId: 202, name: 'Tenant Beta' };

  // 1. Nominal Pipeline Completion (Steps 1 -> 2 -> 3)
  const nominalResult = await coordinator.execute3StepPipeline({
    id: 'pipe-nominal-001',
    failAtStep: null,
    tenantContext: tenantA,
  });
  assert.strictEqual(nominalResult.stage, 'done');
  assert.strictEqual(store.get('pipe-nominal-001', tenantA).stage, 'done');
  assertions += 2;

  // Record baseline store count
  const baselineCount = store.size();

  // 2. Step 2 Fault Injection: Verify Clean Compensating Rollback (0 Orphaned Records)
  const faultId = 'pipe-fault-step2-002';
  let thrownError = null;

  try {
    await coordinator.execute3StepPipeline({
      id: faultId,
      failAtStep: 2,
      tenantContext: tenantA,
    });
  } catch (err) {
    thrownError = err;
  }

  assert(thrownError instanceof AtomicPipelineRollbackError, 'Must throw AtomicPipelineRollbackError');
  assert.strictEqual(thrownError.failedStep, 2, 'Failed step must be 2');
  assert.strictEqual(thrownError.compensationsExecuted, 1, 'Exactly 1 compensation must be executed for Step 1');
  assertions += 3;

  // Invariant: Zero orphaned records left in store after Step 2 failure
  assert.strictEqual(store.size(), baselineCount, 'Store size must strictly revert to baseline after rollback');
  assert.strictEqual(store.records.has(faultId), false, 'Record from aborted pipeline must be completely purged');
  assertions += 2;

  // 3. Multi-Tenant company_id Boundary Access Failure
  // Tenant A creates a private confidential record
  const secretDocId = 'confidential-doc-a1';
  store.insert({ id: secretDocId, secretData: 'CLASSIFIED_ALPHA' }, tenantA);
  assert.strictEqual(store.get(secretDocId, tenantA).secretData, 'CLASSIFIED_ALPHA');
  assertions++;

  // Tenant B attempts to READ Tenant A's record -> MUST throw TenantBoundaryViolationError
  assert.throws(
    () => store.get(secretDocId, tenantB),
    (err) => {
      assert(err instanceof TenantBoundaryViolationError);
      assert.strictEqual(err.expectedCompanyId, tenantA.companyId);
      assert.strictEqual(err.attemptedCompanyId, tenantB.companyId);
      return true;
    },
    'Cross-tenant read must throw TenantBoundaryViolationError'
  );
  assertions++;

  // Tenant B attempts to DELETE Tenant A's record -> MUST throw TenantBoundaryViolationError
  assert.throws(
    () => store.delete(secretDocId, tenantB),
    TenantBoundaryViolationError,
    'Cross-tenant delete must throw TenantBoundaryViolationError'
  );
  assertions++;

  // Tenant B attempts to SPOOF company_id in payload -> MUST throw TenantBoundaryViolationError
  assert.throws(
    () => store.insert({ id: 'spoof-attack-001', companyId: tenantA.companyId }, tenantB),
    TenantBoundaryViolationError,
    'Cross-tenant company_id spoofing must throw TenantBoundaryViolationError'
  );
  assertions++;

  // Verify Tenant Query Partitioning: Zero Cross-Tenant Leakage
  const tenantARecords = store.query(tenantA);
  const tenantBRecords = store.query(tenantB);

  assert(tenantARecords.some((r) => r.id === secretDocId), 'Tenant A must see their record');
  assert(!tenantBRecords.some((r) => r.id === secretDocId), 'Tenant B must NOT see Tenant A records in query');
  assertions += 2;

  console.log(`  ✓ Nominal 3-step pipeline completed cleanly`);
  console.log(`  ✓ Fault injected at Step 2 -> 100% compensating rollback executed`);
  console.log(`  ✓ Zero orphaned records invariant verified: store size strictly reverted`);
  console.log(`  ✓ Multi-tenant company_id boundary access failure: read, delete, and spoof attacks intercepted`);
  console.log(`  ✓ Multi-tenant partition query strictly isolates Tenant A and Tenant B data`);
  console.log(`  [Pass: Vector 4 with ${assertions} verified assertions]`);
  return { vector: 4, passed: true, assertions };
}

// ==============================================================================
// ADVERSARIAL SUITE ORCHESTRATOR
// ==============================================================================

async function runAdversarialSuite() {
  const tStart = Date.now();
  console.log('================================================================================');
  console.log('🛡️  HOOT 4-VECTOR ADVERSARIAL SCENARIO TEST SUITE DIRECTIVE');
  console.log('   Platform: Insilos Enterprise Platform (Odoo 20 LTS Hard Fork)');
  console.log('================================================================================');

  const results = [];
  try {
    results.push(await testVector1StateMachineInvariants());
    results.push(await testVector2ConcurrencyRaceInvariants());
    results.push(await testVector3BoundaryValueStress());
    results.push(await testVector4PartialFailureAndTenancy());
  } catch (err) {
    console.error('\n❌ ADVERSARIAL TEST SUITE FAILED WITH UNHANDLED ERROR:');
    console.error(err.stack || err.message || err);
    return 1;
  }

  const duration = Date.now() - tStart;
  const totalAssertions = results.reduce((sum, r) => sum + r.assertions, 0);

  console.log('\n================================================================================');
  console.log('                    ADVERSARIAL VERIFICATION SUMMARY REPORT                     ');
  console.log('================================================================================');
  console.log(
    'Vector'.padEnd(12) +
      'Description'.padEnd(46) +
      'Status'.padEnd(12) +
      'Assertions'
  );
  console.log('-'.repeat(80));

  const descriptions = [
    'State Machine Invariant Proof (S x E -> S\')',
    'Concurrency Race & Optimistic Locking',
    'Boundary Value Stress & Poison Pills',
    'Partial Failure Rollback & Multi-Tenant',
  ];

  for (let i = 0; i < results.length; i++) {
    const r = results[i];
    const vecLabel = `Vector ${r.vector}`.padEnd(12);
    const desc = descriptions[i].padEnd(46);
    const status = (r.passed ? '✅ PASS' : '❌ FAIL').padEnd(12);
    const count = String(r.assertions);
    console.log(`${vecLabel}${desc}${status}${count}`);
  }

  console.log('='.repeat(80));
  console.log(`TOTAL VECTORS   : ${results.length}/4 passed (100%)`);
  console.log(`TOTAL ASSERTIONS: ${totalAssertions} verified invariant conditions`);
  console.log(`TOTAL RUNTIME   : ${duration}ms`);
  console.log('================================================================================');
  console.log('🎉 ALL 4 ADVERSARIAL VECTORS PASSED 100% WITH ZERO INVARIANT VIOLATIONS!\n');

  return 0;
}

module.exports = {
  runAdversarialSuite,
  DomainStateError,
  OptimisticLockError,
  PoisonPillValidationError,
  AtomicPipelineRollbackError,
  TenantBoundaryViolationError,
  DocumentStateMachine,
  OptimisticRecordStore,
  SafePayloadHandler,
  MultiTenantStore,
  AtomicPipelineCoordinator,
  States,
  Events,
};

if (require.main === module) {
  runAdversarialSuite()
    .then((code) => {
      process.exit(code);
    })
    .catch((err) => {
      console.error('Fatal suite execution error:', err);
      process.exit(1);
    });
}
