#!/usr/bin/env python3
# FROZEN HISTORICAL RECORD: reproduces hash-ledgered results; domain-specific by nature.
# Do not modify. New experiments use src/core (neutral) + src/domains/<domain>.py.
"""Structure discovery in apparently random data — theorem-based instruments.

Dataset: 776 draws, treated purely as a sequence from an unknown source.
Three independent mathematical certificates:

I.   SHANNON / KOLMOGOROV (source coding theorem + incompressibility):
     Any computable regularity allows compression below the entropy bound
     H = log2 C(P,6) bits/draw. We bit-pack the sequence and attack it with
     LZMA/zlib/bz2. Compressed size < Shannon bound  =>  structure exists.
     (One-sided certificate: compressors can fail to find structure, but
     cannot compress true randomness below H except with prob 2^-k.)

II.  RANDOM MATRIX THEORY (Marchenko-Pastur law):
     The eigenvalue spectrum of a T x P random correlation matrix converges
     to the MP density on [(1-sqrt(P/T))^2, (1+sqrt(P/T))^2]. Eigenvalues
     escaping the bulk = collective modes (factors) in the data. The fixed
     row-sum (exactly 6 ones per draw) is a known constraint producing one
     trivial null direction, so the null band is calibrated by Monte Carlo
     of the constrained ensemble, with the literal MP edges as reference.

III. WIENER-KHINCHIN + FISHER'S g-TEST (hidden periodicities):
     White noise has a flat expected periodogram; Fisher's exact g-statistic
     g = max_k I(w_k) / sum_k I(w_k) tests the largest spectral peak with
     p ~= N(1-g)^(N-1). Detects clocks, maintenance cycles, seasonal effects.
"""
import csv, math, lzma, zlib, bz2, random
import numpy as np

random.seed(3); np.random.seed(3)
POOLS = {"Lotto 6/42": 42, "Mega Lotto 6/45": 45, "Super Lotto 6/49": 49,
         "Grand Lotto 6/55": 55, "Ultra Lotto 6/58": 58}

def load():
    out = {g: [] for g in POOLS}
    for r in csv.reader(open("datasets/pcso-lotto/data_draws_1yr.csv")):
        if r and r[0] in POOLS:
            out[r[0]].append((r[1], sorted(int(x) for x in r[2:8])))
    return {g: [s for _, s in sorted(v)] for g, v in out.items()}

def bitpack(draws, P):
    bits = []
    for d in draws:
        row = [0] * P
        for n in d: row[n - 1] = 1
        bits += row
    bits += [0] * (-len(bits) % 8)  # pad to byte boundary (code review fix: bits were dropped)
    by = bytearray()
    for i in range(0, len(bits), 8):
        by.append(int("".join(map(str, bits[i:i+8])), 2))
    return bytes(by)

def certificate_I(data):
    print("\nI. COMPRESSION CERTIFICATE (source coding theorem)")
    print(f"{'game':18s}{'Shannon bound':>14s}{'best compressed':>16s}{'raw':>8s}  verdict")
    for g, P in POOLS.items():
        nd = len(data[g])
        H = nd * math.log2(math.comb(P, 6))
        raw = bitpack(data[g], P)
        co = zlib.compressobj(9, zlib.DEFLATED, -15)  # raw DEFLATE, no container header
        deflate = co.compress(raw) + co.flush()
        best = min(len(lzma.compress(raw, preset=9)), len(zlib.compress(raw, 9)),
                   len(bz2.compress(raw, 9)), len(deflate)) * 8
        verdict = "STRUCTURE (compressible!)" if best < H else "incompressible (random-like)"
        print(f"{g:18s}{H:12.0f} b{best:14d} b{len(raw)*8:7d} b  {verdict}")

def certificate_II(data, nsim=1000):
    print("\nII. MARCHENKO-PASTUR CERTIFICATE (random matrix theory)")
    print(f"{'game':18s}{'lam_max':>8s}{'MC null 99%':>12s}{'MP edge':>9s}{'escaped':>9s}")
    for g, P in POOLS.items():
        draws = data[g]; T = len(draws)
        def spectrum(ds):
            X = np.zeros((len(ds), P))
            for t, d in enumerate(ds):
                for n in d: X[t, n - 1] = 1
            X = (X - X.mean(0)) / (X.std(0) + 1e-12)
            return np.linalg.eigvalsh(X.T @ X / len(ds))
        ev = spectrum(draws)
        null_max = sorted(max(spectrum([sorted(random.sample(range(1, P+1), 6))
                                        for _ in range(T)])) for _ in range(nsim))
        q99 = null_max[int(0.99 * nsim)]
        mp_edge = (1 + math.sqrt(P / T)) ** 2
        esc = sum(1 for v in ev if v > q99)
        print(f"{g:18s}{max(ev):8.3f}{q99:12.3f}{mp_edge:9.3f}{esc:9d}")

def certificate_III(data):
    print("\nIII. FISHER g-TEST CERTIFICATE (hidden periodicities)")
    print(f"{'game':18s}{'g':>8s}{'p-value':>9s}{'peak period':>12s}")
    for g, P in POOLS.items():
        x = np.array([sum(d) / 6 for d in data[g]], dtype=float)
        x = (x - x.mean()) / x.std()
        I = np.abs(np.fft.rfft(x)[1:len(x)//2]) ** 2
        N = len(I)
        gstat = I.max() / I.sum()
        # Fisher's exact p: sum_j (-1)^(j-1) C(N,j) (1-jg)^(N-1) over jg<1
        p = sum((-1) ** (j - 1) * math.comb(N, j) * (1 - j * gstat) ** (N - 1)
                for j in range(1, min(N, int(1 / gstat)) + 1))
        p = max(0.0, min(1.0, p))
        period = len(x) / (np.argmax(I) + 1)
        print(f"{g:18s}{gstat:8.4f}{p:9.3f}{period:10.1f} draws")

if __name__ == "__main__":
    data = load()
    print(f"STRUCTURE DISCOVERY SUITE — {sum(len(v) for v in data.values())} draws as abstract sequence")
    certificate_I(data)
    certificate_II(data)
    certificate_III(data)
    print("\nInterpretation: structure exists iff any certificate fires "
          "(compression below H, eigenvalue escape, or significant spectral peak).")
