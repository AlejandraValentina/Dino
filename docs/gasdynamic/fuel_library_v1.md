# FUEL_LIBRARY_V1

The library stores versioned fuel definitions and provenance snapshots. It does
not configure fuel delivery, trapping, combustion, lubrication, or heat release.
The snapshot records fuel ID, version, complete canonical definition, and
SHA-256; a later library edit cannot change an existing simulation snapshot.

## ANCAP catalog scope

The built-in `ANCAP_SUPER_95` and `ANCAP_PREMIUM_97` profiles preserve product
identity and RON from ANCAP. They deliberately leave density, LHV, elemental
composition, actual ethanol fraction, and stoichiometric AFR unknown. ANCAP's
2024-06 datasheets specify limits (including up to 10% ethanol by volume and
maximum oxygen levels), not exact batch composition. A maximum is not used as a
measured or modeled point value. Both profiles therefore remain ineligible for
chemistry-derived AFR or energy outputs until explicit supported properties
are supplied.

Primary sources checked 2026-10-06:

- Súper 95 product page: <https://www.ancap.com.uy/1636/5/super-95.html>
- Súper 95 datasheet 2024-06-24:
  <https://exploracionyproduccion.ancap.com.uy/innovaportal/file/1636/1/gasolina-super-95--2024-06-24.pdf>
- Premium 97 product page: <https://www.ancap.com.uy/1637/6/premium-97.html>
- Premium 97 datasheet 2024-06-24:
  <https://www.ancap.com.uy/innovaportal/file/1637/1/gasolina-premium-97-euro-5-2024-06-24.pdf>

The product pages identify RON 95 and RON 97 and state that anhydrous ethanol
may be added up to 10% by volume. The datasheets give RON specifications and
maximum ethanol/oxygen content. The available material did not establish a
point density, LHV, elemental composition, or stoichiometric AFR for either
product. No ANCAP values have been inferred from name or octane.

## Elemental stoichiometry

When a user profile includes complete elemental mass fractions, missing
stoichiometric AFR can be derived using the versioned method
`ELEMENTAL_MASS_BALANCE_DRY_AIR_V1`:

```text
n_O2 = w_C/M_C + (w_H/M_H)/4 + w_S/M_S - (w_O/M_O)/2
AFR_st = n_O2 * M_O2 / 0.232
```

Atomic/molecular masses, dry-air oxygen mass fraction, and the algorithm version
are included in the implementation. Nonpositive oxygen demand is rejected.
This derives only a stoichiometric property; it does not add reaction chemistry
or combustion behavior to the engine model. A `MODELED_SURROGATE` must have an
explicit version and its own provenance; no such surrogate is included by this
initial library change.

The 2T lubricant and premix ratio are separate future interfaces. The current
fuel library does not model oil combustion.
