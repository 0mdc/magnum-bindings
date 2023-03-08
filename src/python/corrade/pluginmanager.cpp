/*
    This file is part of Magnum.

    Copyright © 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
                2020, 2021, 2022 Vladimír Vondruš <mosra@centrum.cz>

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
*/

#include <pybind11/pybind11.h>
#include <pybind11/stl.h> /* for pluginList() and aliasList() */
#include <Corrade/Containers/Array.h>
#include <Corrade/Containers/StringStl.h> /** @todo drop once we have our string casters */
#include <Corrade/Containers/StringIterable.h>
#include <Corrade/PluginManager/AbstractManager.h>

#include "Corrade/PythonBindings.h"

#include "corrade/bootstrap.h"
#include "corrade/EnumOperators.h"

namespace corrade {

void pluginmanager(py::module_& m) {
    m.doc() = "Plugin management";

    py::enum_<PluginManager::LoadState> loadState{m, "LoadState", "Plugin load state"};
    loadState
        .value("NOT_FOUND", PluginManager::LoadState::NotFound)
        .value("WRONG_PLUGIN_VERSION", PluginManager::LoadState::WrongPluginVersion)
        .value("WRONG_INTERFACE_VERSION", PluginManager::LoadState::WrongInterfaceVersion)
        .value("WRONG_METADATA_FILE", PluginManager::LoadState::WrongMetadataFile)
        .value("UNRESOLVED_DEPENDENCY", PluginManager::LoadState::UnresolvedDependency)
        .value("STATIC", PluginManager::LoadState::Static)
        .value("LOADED", PluginManager::LoadState::Loaded)
        .value("NOT_LOADED", PluginManager::LoadState::NotLoaded)
        .value("UNLOAD_FAILED", PluginManager::LoadState::UnloadFailed)
        .value("REQUIRED", PluginManager::LoadState::Required)
        .value("USED", PluginManager::LoadState::Used);
    corrade::enumOperators(loadState);

    PyNonDestructibleClass<PluginManager::AbstractManager> manager{m, "AbstractManager", "Base for plugin managers"};
    manager.attr("VERSION") = PluginManager::AbstractManager::Version;
    manager
        .def_property_readonly("plugin_interface", [](PluginManager::AbstractManager& self) {
            /** @todo drop std::string in favor of our own string caster */
            return std::string{self.pluginInterface()};
        }, "Plugin interface string")
        .def_property("plugin_directory",
            /** @todo drop std::string in favor of our own string caster */
            [](PluginManager::AbstractManager& self) {
                return std::string{self.pluginDirectory()};
            }, [](PluginManager::AbstractManager& self, const std::string& directory) {
                self.setPluginDirectory(directory);
            }, "Plugin directory")
        .def("reload_plugin_directory", &PluginManager::AbstractManager::reloadPluginDirectory, "Reload plugin directory")
        .def("set_preferred_plugins", [](PluginManager::AbstractManager& self, const std::string& alias, const std::vector<std::string>& plugins) {
            if(self.loadState(alias) == PluginManager::LoadState::NotFound) {
                PyErr_SetNone(PyExc_KeyError);
                throw py::error_already_set{};
            }

            /** @todo drop all this once StringIterable can be a view on
                std::strings */
            Containers::Array<Containers::StringView> pluginViews{NoInit, plugins.size()};
            for(std::size_t i = 0; i != plugins.size(); ++i)
                pluginViews[i] = plugins[i];
            self.setPreferredPlugins(alias, pluginViews);
        }, "Set preferred plugins for given alias", py::arg("alias"), py::arg("plugins"))
        .def_property_readonly("plugin_list", [](PluginManager::AbstractManager& self) {
            /** @todo make a generic caster for arbitrary arrays and strings */
            std::vector<std::string> out;
            for(Containers::StringView i: self.pluginList())
                out.push_back(i);
            return out;
        }, "List of all available plugin names")
        .def_property_readonly("alias_list", [](PluginManager::AbstractManager& self) {
            /** @todo make a generic caster for arbitrary arrays and strings */
            std::vector<std::string> out;
            for(Containers::StringView i: self.aliasList())
                out.push_back(i);
            return out;
        }, "List of all available alias names")
        /** @todo metadata() (figure out the ownership) */
        /** @todo drop std::string in favor of our own string caster */
        .def("load_state", [](PluginManager::AbstractManager& self, const std::string& plugin) {
            return self.loadState(plugin);
        }, "Load state of a plugin", py::arg("plugin"))
        .def("load", [](PluginManager::AbstractManager& self, const std::string& plugin) {
            /** @todo log redirection -- but we'd need assertions to not be
                part of that so when it dies, the user can still see why */
            const PluginManager::LoadState state = self.load(plugin);
            if(!(state & PluginManager::LoadState::Loaded)) {
                PyErr_Format(PyExc_RuntimeError, "can't load plugin %s", plugin.data());
                throw py::error_already_set{};
            }

            return state;
        }, "Load a plugin", py::arg("plugin"))
        .def("unload", [](PluginManager::AbstractManager& self, const std::string& plugin) {
            /** @todo log redirection -- but we'd need assertions to not be
                part of that so when it dies, the user can still see why */
            const PluginManager::LoadState state = self.unload(plugin);
            if(state != PluginManager::LoadState::NotLoaded && state != PluginManager::LoadState::Static) {
                PyErr_Format(PyExc_RuntimeError, "can't unload plugin %s", plugin.data());
                throw py::error_already_set{};
            }

            return state;
        }, "Unload a plugin", py::arg("plugin"));
}

}

#ifndef CORRADE_BUILD_STATIC
extern "C" PYBIND11_EXPORT PyObject* PyInit_pluginmanager();
PYBIND11_MODULE(pluginmanager, m) {
    corrade::pluginmanager(m);
}
#endif
