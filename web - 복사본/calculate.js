/**
 * N/B MAX, N/B MIN 계산 엔진
 */

function initializeArrays(count) {
    const arrays = ['BIT_START_A50', 'BIT_START_A100', 'BIT_START_B50', 'BIT_START_B100', 'BIT_START_NBA100'];
    const initializedArrays = {};
    arrays.forEach(array => {
        initializedArrays[array] = new Array(count).fill(0);
    });
    return initializedArrays;
}

function calculateNB(nb, bit = 999, reverse = false) {
    if (nb.length < 2) {
        return bit / 100;
    }

    const BIT_NB = bit;
    const max = Math.max(...nb);
    const min = Math.min(...nb);
    const COUNT = 50;
    const CONT = 20;
    const range = max - min;

    const negativeRange = min < 0 ? Math.abs(min) : 0;
    const positiveRange = max > 0 ? max : 0;

    const negativeIncrement = negativeRange / (COUNT * nb.length - 1);
    const positiveIncrement = positiveRange / (COUNT * nb.length - 1);

    const arrays = initializeArrays(COUNT * nb.length);
    let count = 0;
    let totalSum = 0;

    for (let value of nb) {
        for (let i = 0; i < COUNT; i++) {
            const BIT_END = 1;

            const A50 = value < 0
                ? min + negativeIncrement * (count + 1)
                : min + positiveIncrement * (count + 1);

            const A100 = (count + 1) * BIT_NB / (COUNT * nb.length);

            const B50 = value < 0
                ? A50 - negativeIncrement * 2
                : A50 - positiveIncrement * 2;

            const B100 = value < 0
                ? A50 + negativeIncrement
                : A50 + positiveIncrement;

            const NBA100 = A100 / (nb.length - BIT_END);

            arrays.BIT_START_A50[count] = A50;
            arrays.BIT_START_A100[count] = A100;
            arrays.BIT_START_B50[count] = B50;
            arrays.BIT_START_B100[count] = B100;
            arrays.BIT_START_NBA100[count] = NBA100;

            count++;
        }
    }

    let MAX_BIT_START = 0;
    let MIN_BIT_START = Infinity;
    let result = 0;

    for (let i = 0; i < count; i++) {
        const A50 = arrays.BIT_START_A50[i];
        const A100 = arrays.BIT_START_A100[i];
        const B50 = arrays.BIT_START_B50[i];
        const B100 = arrays.BIT_START_B100[i];
        const NBA100 = arrays.BIT_START_NBA100[i];

        const A = (A50 + A100) / 2;
        const B = (B50 + B100) / 2;

        const START = Math.abs(A - B) / 2;

        if (START > MAX_BIT_START) {
            MAX_BIT_START = START;
        }

        if (START < MIN_BIT_START) {
            MIN_BIT_START = START;
        }

        if (reverse) {
            result += NBA100 / (START + 0.0000001);
        } else {
            result += START * NBA100;
        }
    }

    result = result / count;

    if (!isFinite(result) || isNaN(result)) {
        result = bit / 100;
    }

    return result;
}

module.exports = {
    calculateNB
};
