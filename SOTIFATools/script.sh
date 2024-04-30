PROCESS_DIR=$MY_SCRIPT_ARG1
echo "${1}"
echo "${2}"
echo "${3}"
echo "${4}"
echo "${5}"
echo "${6}"
echo "${7}"
echo "${8}"
echo "${9}"
echo "${10}"
echo "${11}"
echo "${12}"
echo "${13}"
echo "${14}"
echo "${15}"
echo "${61}"

java -cp $PROCESS_DIR evaluation/Program1 "${1}" "${@:16}" & 
java -cp $PROCESS_DIR evaluation/Program2 "${2}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program3 "${3}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program4 "${4}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program5 "${5}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program6 "${6}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program7 "${7}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program8 "${8}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program9 "${9}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program10 "${10}" "${@:16}" &

java -cp $PROCESS_DIR evaluation/Program11 "${11}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program12 "${12}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program13 "${13}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program14 "${14}" "${@:16}" &
java -cp $PROCESS_DIR evaluation/Program15 "${15}" "${@:16}" &
