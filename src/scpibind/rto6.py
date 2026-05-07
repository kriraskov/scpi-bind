import numpy as np
from src.scpibind.instrument import Instrument, SubSystem, SCPIProperty


class RTO6(Instrument):
    def __init__(
        self,
        resource_name: str,
        name: str = "RTO6",
        **kwargs
    ) -> None:
        super().__init__(resource_name, name, **kwargs)
        self.channel = [Channel(self, i + 1) for i in range(4)]
        self.math = [Math(self, i + 1) for i in range(8)]
        self.fft = [FFT(self, i + 1) for i in range(8)]

    format = SCPIProperty("FORM?")
    update_display = SCPIProperty("SYST:DISP:UPD?")

    def single(self):
        self.write("RUNS")


class Channel(SubSystem):
    status = SCPIProperty("CHAN{suffix}:STAT?")
    coupling = SCPIProperty("CHAN{suffix}:COUP?")

    def setup(self, **kwargs) -> None:
        super().setup(status='ON', **kwargs)


class Math(SubSystem):
    status = SCPIProperty("CALC:MATH{suffix}:STAT?")
    expression = SCPIProperty("CALC:MATH{suffix}:EXPR?")
    range = SCPIProperty("CALC:MATH{suffix}:VERT:RANG?")
    header = SCPIProperty("CALC:MATH{suffix}:DATA:HEAD?")

    def setup(self, **kwargs) -> None:
        super().setup(status='ON', **kwargs)

    def get_data(self):
        return self.query_binary_values(
            f"CALC:MATH{self.suffix}:DATA?",
            datatype="f",
            container=np.array
        )


class FFT(SubSystem):
    type = SCPIProperty("CALC:MATH{suffix}:FFT:TYPE?")
    logscale = SCPIProperty("CALC:MATH{suffix}:FFT:LOGS?")
    window = SCPIProperty("CALC:MATH{suffix}:FFT:WIND:TYPE?")
    start = SCPIProperty("CALC:MATH{suffix}:FFT:START?")
    stop = SCPIProperty("CALC:MATH{suffix}:FFT:STOP?")
    bandwidth = SCPIProperty("CALC:MATH{suffix}:FFT:BAND?")
    level = SCPIProperty("CALC:MATH{suffix}:FFT:MAGN:LEV?")
    count = SCPIProperty("CALC:MATH{suffix}:FFT:FRAM:MAXC?")
    overlap = SCPIProperty("CALC:MATH{suffix}:FFT:FRAM:OFAC?")
