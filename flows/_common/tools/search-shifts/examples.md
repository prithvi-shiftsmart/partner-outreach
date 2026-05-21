# search_shifts -- Examples

## Default (quality score)
Input: partner_id: "p_abc123"
Output:
{
  "shifts": [
    { "shift_id": "s_001", "role": "Food Prep -- Lunch", "pay": 22.75, "bonus": 0, "date": "Tue 5/13", "time": "9:30-11:15 AM", "distance_mi": 6.2, "address": "4501 S Padre Island Dr, Corpus Christi, TX", "brand": "Circle K", "quality_score": 92, "slots_remaining": 3 },
    { "shift_id": "s_002", "role": "Stocking -- Morning", "pay": 19.50, "bonus": 20.00, "date": "Wed 5/14", "time": "6:00-10:00 AM", "distance_mi": 8.4, "address": "2810 Ayers St, Corpus Christi, TX", "brand": "Circle K", "quality_score": 87, "slots_remaining": 1 },
    { "shift_id": "s_003", "role": "Cashier -- Afternoon", "pay": 19.00, "bonus": 0, "date": "Thu 5/15", "time": "1:00-5:00 PM", "distance_mi": 9.1, "address": "1810 SPID, Corpus Christi, TX", "brand": "Circle K", "quality_score": 81, "slots_remaining": 2 }
  ]
}

## No shifts available
Input: partner_id: "p_abc123", time_window: "evening"
Output: { "shifts": [] }
