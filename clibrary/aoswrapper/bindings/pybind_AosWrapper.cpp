#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "AosWrapper.h"

namespace py = pybind11;

PYBIND11_MODULE(aoswrapper, m)
{
    m.doc() = "Python bindings for AosWrapper using pybind11";

    py::class_<AosWrapper>(m, "AosWrapper")
        .def(py::init<>())
        .def("push_back", [](AosWrapper& self, py::bytes data) {
                 std::string buf = data;
                 return self.push_back(buf.data(), (unsigned int)buf.size()); }, py::arg("data"), "Push binary data into the internal buffer.")
        .def("make_mpdu", [](AosWrapper& self, int mpdu_sz, bool force_pop) {
                 unsigned short head_ptr = 0;
                 std::vector<char> head(mpdu_sz, 0);
                 int ret = self.make_mpdu(head_ptr, head.data(), mpdu_sz, force_pop);
                 return py::make_tuple(ret, head_ptr, py::bytes(head.data(), mpdu_sz)); }, py::arg("mpdu_sz"), py::arg("force_pop") = false, "Generate one MPDU frame. Returns (ret, head_ptr, head_bytes).");
}
