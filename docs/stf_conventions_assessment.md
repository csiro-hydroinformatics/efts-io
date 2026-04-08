
---

## Assessment: Code Departures from STF 2.0 Conventions and Bugs

### A. Dimension Ordering on Write

**Spec (Fortran order):** `(lead_time, station, ens_member, time)` → C-order equivalent: `(time, ens_member, station, lead_time)`

**Code:** `_prepare_data` in _ncdf_stf2.py sets:
```python
dimensions_order = (TIME_DIMNAME, ENS_MEMBER_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME)
```

This is `(time, ens_member, station, lead_time)`, which is the correct C-order transposition of the spec's Fortran-order declaration. **Consistent with interpretation, but undocumented.** If a reader interprets the spec literally as C-order, files produced by this code will differ.

### B. Data Variable Written as `float` Instead of `double`

The spec's Description of Variables section says observed and simulated data are "double". The code at _ncdf_stf2.py uses `"f"` (32-bit float):

```python
var = nc.createVariable(naming.short_name, "f", ...)
```

This is a departure from the spec's "double" declaration. If the user sets `precision='double'` in their variable definition, it is ignored at this point — the netCDF dtype is always `"f"`.

### C. Quality Code Variable Written as `float` Instead of `int`

The spec says quality code `_FillValue` is `int | -1`, implying an integer type. The code at _ncdf_stf2.py writes it as `"f"` (float):

```python
var = nc.createVariable(qu_var_name_s, "f", dims, fill_value=-1)
```

Additionally, the quality variable's dimension order for STF v2 is `(time, ens_member, station, lead_time)`, which matches the main data variable but **not the spec's stated order** `(lead_time, station, ens_member, time)` (again, likely a Fortran/C order interpretation issue, but the quality variable follows the same convention as the data variable, which is at least self-consistent).

### D. `STF_convention_version` Written as String

The spec says this should be a `float`. In wrapper.py and wrapper.py, the value is set as the **string** `"2.0"`:

```python
self.stf_convention_version = "2.0"
```
```python
STF_CONVENTION_VERSION_ATTR_KEY: "2.0",
```

The property type hint says `float`, but a string is assigned. The `create_global_attributes` function in attributes.py correctly defaults to `2.0` (float), so there is an inconsistency between code paths.

### E. `lead_time` Units Hardcoded to `"days since time"` on Write

In `_write_lead_time_dimension` at _ncdf_stf2.py, the lead_time units are always `"days since time"`, ignoring the user's `timestep` parameter:

```python
UNITS_ATTR_KEY: "days since time",
```

The `timestep` argument only controls the **time** dimension units, not lead_time. If the user has hourly lead times, the written file will still claim `"days since time"`.

### F. `x` / `y` Standard Name Swap in `default_optional_variable_definitions_v2_0`

In variables.py, the `name` column has `["x", "y", ...]` but the `standard_name` column has `["northing_GDA94_zone55", "easting_GDA94_zone55", ...]`. The spec says:
- `x` → `standard_name` = `"easting_GDA94_zone55"`
- `y` → `standard_name` = `"northing_GDA94_zone55"`

**The standard names are swapped**: `x` is assigned `"northing..."` and `y` is assigned `"easting..."`. Likewise the `longname` values are swapped: `x` gets `"easting..."` and `y` gets `"northing..."` — the long names are correct relative to the `name`, but the `standard_name` values contradict them.

### G. Latitude/Longitude Units Inconsistency in Legacy Path

In variables.py (the `create_mandatory_vardefs` path), units are `"degrees north"` and `"degrees east"` (with space). In the write path (_ncdf_stf2.py) and `xr_efts` (wrapper.py), they are `"degrees_north"` and `"degrees_east"` (with underscore, matching the spec). The legacy path is non-conformant.

### H. `area` Units Differ from Spec

The spec says `area` units should be `"sqm"` (square metres). The code uses `"km^2"` (square kilometres) in variables.py and wrapper.py. This is arguably an improvement over the spec's non-standard `"sqm"`, but it is a deliberate departure.

### I. `dat_type_description` Attribute Ignores User-Provided Value

In `_write_data_variable` at _ncdf_stf2.py:

```python
var.setncattr(DAT_TYPE_DESCRIPTION_ATTR_KEY, naming.dat_type_description)
```

Unlike `dat_type`, `type`, `type_description`, and `location_type` — which all fall back to user-provided `data_attrs` — `dat_type_description` always uses the value from `VariableNaming`, overriding any user-specified description. This is a bug: the user cannot customise this attribute through the normal attribute flow.

### J. `station_name` Dimensions: `(station, strLen)` vs Spec's `(strLen, station)`

The spec declares `station_name(strLen, station)`. The write code at _ncdf_stf2.py uses:
```python
nc.createVariable(STATION_NAME_VARNAME, "c", (STATION_DIMNAME, STR_LEN_DIMNAME))
```

This is `(station, strLen)` — the transposition of the spec. Given the Fortran/C ordering ambiguity (point 10 of the assessment), this is arguably correct for C-order and matches the idiomatic way to store an array of strings. However, the legacy `create_mandatory_vardefs` in variables.py uses `dims=[str_dim[0], STATION_DIMNAME]` i.e. `(strLen, station)`, so the two code paths are **mutually inconsistent**.

### K. `time` Variable Written as Integer

The spec's Dimensions section says `time` is `NF90_FLOAT`; the Description says `int32`. The code writes `time` using `self._intdata_type` (default `"i4"` = 32-bit integer) at _ncdf_stf2.py. The code follows the `int32` interpretation consistently, but files will differ from implementations that follow the `NF90_FLOAT` declaration.

### L. `time_standard` Attribute Set to `"UTC{offset}"` Instead of `"UTC"`

The spec says the `time_standard` example is `"UTC"`. The code at _ncdf_stf2.py writes:
```python
TIME_STANDARD_ATTR_KEY: f"UTC{timezone_offset}",
```
producing values like `"UTC+10:00"`. This is an extension beyond the spec (which only shows `"UTC"`), but is a reasonable enhancement for timezone-aware data.

### M. `STF_nc_spec` URL Points to a GitHub Commit, Not the Wiki

The spec example says `STF_nc_spec = 'https://wiki.csiro.au/display/wirada/...'`. The code uses a commit-pinned GitHub URL (conventions.py). Functionally sensible, but non-conformant with the example value.

### N. Missing `standard_name` Attribute on `time` and `station` Variables in `xr_efts`

The `xr_efts` function sets `standard_name` on `time` and `lead_time` coordinates but not on `station_id`. The spec requires `standard_name` only on `time`, `ens_member`, and `lead_time` — so this is fine. However, `station_id` and `station_name` lack `standard_name` in the spec too, so no issue here.

### O. `area` Long Name: `"station area"` vs `"catchment area"`

The `xr_efts` path uses `"station area"` (wrapper.py), matching the spec. The legacy `default_optional_variable_definitions_v2_0` uses `"catchment area"` (variables.py). Minor inconsistency between code paths.

---

### Summary of Most Consequential Issues

| # | Severity | Issue |
|---|----------|-------|
| B | **High** | Data variables always written as `float` (32-bit), spec says `double` (64-bit) — precision loss |
| I | **High** | `dat_type_description` user value silently ignored on write |
| F | **Medium** | `x`/`y` standard names are swapped in defaults |
| E | **Medium** | `lead_time` units hardcoded to `"days since time"`, ignores actual lead time step |
| D | **Medium** | `STF_convention_version` written as string `"2.0"` instead of float `2.0` in key code paths |
| C | **Medium** | Quality variable type is `float` not `int` |
| J | **Medium** | `station_name` dimension order inconsistent between write paths |
| G | **Low** | Lat/lon units `"degrees north"` (legacy) vs `"degrees_north"` (write) |
| H | **Low** | `area` units `"km^2"` vs spec's `"sqm"` (intentional improvement) |