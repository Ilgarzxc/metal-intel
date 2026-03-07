parts = ["2015"]

while len(parts) < 3:
    parts.append("01")

date = "-".join(parts)
print(date)