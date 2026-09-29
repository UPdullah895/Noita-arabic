-- Noita lays out wand/spell tooltip rows 8px apart, read from one float in the
-- executable's writable .data section. Arabic needs more room than Latin, so
-- raise it at startup. Only touches memory when this exact build is running:
-- the float must still be 8.0 and a known tooltip instruction must reference it.
local ffi = require("ffi")

local ROW_PITCH = ffi.cast("float*", 0x0115331C)
local CHECK_AT  = ffi.cast("uint8_t*", 0x00B6A044)  -- addss xmm0, [0x115331C]
local EXPECTED  = { 0xF3, 0x0F, 0x58, 0x05, 0x1C, 0x33, 0x15, 0x01 }
local NEW_PITCH = 11

local function build_matches()
    for i, byte in ipairs(EXPECTED) do
        if CHECK_AT[i - 1] ~= byte then return false end
    end
    return ROW_PITCH[0] == 8
end

if build_matches() then
    ROW_PITCH[0] = NEW_PITCH
    print("[arabic_tooltip_spacing] tooltip row pitch 8 -> " .. NEW_PITCH)
else
    print("[arabic_tooltip_spacing] unknown Noita build, leaving tooltips alone")
end
