import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

# from verify import main as verify_main
from translate.translate import main as translate_main
# from groundtruth_check.GroundTruth_Check import main as ground_truth_check_main

print("======================================")
print("Start the Process...\n")
print("Start to Translate...\n======================================")
try:
    translate_main()
except Exception as e:
    print(f"Error during translation: {e}")
    print("Please check the input file and translation settings.")
    sys.exit(1)
print("======================================\nTranslate Finished...")
# print("\nStart to Verify...\n======================================")
# try:
#     verify_main()
# except Exception as e:
#     print(f"Error during verification: {e}")
#     print("Please check the verification settings.")
#     sys.exit(1)
# print("======================================\nVerify Finished...\n")
# print("Start to Check Ground Truth...\n======================================")
# try:
#     ground_truth_check_main()
# except Exception as e:
#     print(f"Error during ground truth check: {e}")
#     print("Please check the ground truth settings.")
#     sys.exit(1)
# print("Process Finished...\n======================================")