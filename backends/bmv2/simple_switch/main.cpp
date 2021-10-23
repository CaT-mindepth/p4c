/*
Copyright 2013-present Barefoot Networks, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

#include <stdio.h>
#include <string>
#include <iostream>

#include "ir/ir.h"
#include "control-plane/p4RuntimeSerializer.h"
#include "frontends/common/applyOptionsPragmas.h"
#include "frontends/common/parseInput.h"
#include "frontends/p4/frontend.h"
#include "lib/error.h"
#include "lib/exceptions.h"
#include "lib/gc.h"
#include "lib/log.h"
#include "lib/nullstream.h"
#include "backends/bmv2/common/JsonObjects.h"
#include "backends/bmv2/simple_switch/midend.h"
#include "backends/bmv2/simple_switch/simpleSwitch.h"
#include "backends/bmv2/simple_switch/version.h"
#include "backends/bmv2/simple_switch/options.h"
#include "ir/json_loader.h"
#include "fstream"

extern const char* pkt_field_table_info;
extern const char* file_for_dep_info;

const char* pkt_field_table_info;
const char* file_for_dep_info;
int main(int argc, char *const argv[]) {
    // for (int i = 0; i < argc; i++) {
    //     std::cout << "argv[" << i << "] = " << argv[i] << std::endl;
    // }
    setup_gc_logging();

    AutoCompileContext autoBMV2Context(new BMV2::SimpleSwitchContext);
    auto& options = BMV2::SimpleSwitchContext::get().options();
    options.langVersion = CompilerOptions::FrontendVersion::P4_16;
    options.compilerVersion = BMV2_SIMPLESWITCH_VERSION_STRING;

    if (options.process(argc, argv) != nullptr) {
            if (options.loadIRFromJson == false)
                    options.setInputFile();
    }
    if (::errorCount() > 0)
        return 1;

    auto hook = options.getDebugHook();

    // BMV2 is required for compatibility with the previous compiler.
    options.preprocessor_options += " -D__TARGET_BMV2__";

    const IR::P4Program *program = nullptr;
    const IR::ToplevelBlock* toplevel = nullptr;


    if (options.loadIRFromJson == false) {
        program = P4::parseP4File(options);
        // std::cout << "program = " << program << std::endl;
        // if (program == nullptr || ::errorCount() > 0)
        //    return 1;
        // std::cout << "program = " << program << std::endl;
        try {
            P4::P4COptionPragmaParser optionsPragmaParser;
	    std::cout << "Before apply" << std::endl;
            program->apply(P4::ApplyOptionsPragmas(optionsPragmaParser));
	    std::cout << "After apply" << std::endl;
            P4::FrontEnd frontend;
            frontend.addDebugHook(hook);
            program = frontend.run(options, program);
            // std::cout << "program = " << program << std::endl;
        } catch (const std::exception &bug) {
            std::cerr << bug.what() << std::endl;
            return 1;
        }
        if (program == nullptr || ::errorCount() > 0)
            return 1;
    } else {
        std::filebuf fb;
        if (fb.open(options.file, std::ios::in) == nullptr) {
            ::error("%s: No such file or directory.", options.file);
            return 1;
        }
        std::istream inJson(&fb);
        JSONLoader jsonFileLoader(inJson);
        if (jsonFileLoader.json == nullptr) {
            ::error("Not valid input file");
            return 1;
        }
        program = new IR::P4Program(jsonFileLoader);
        fb.close();
    }

    P4::serializeP4RuntimeIfRequired(program, options);
    if (::errorCount() > 0)
        return 1;
    BMV2::SimpleSwitchMidEnd midEnd(options);
    midEnd.addDebugHook(hook);
    try {
        toplevel = midEnd.process(program);
        if (::errorCount() > 1 || toplevel == nullptr ||
            toplevel->getMain() == nullptr)
            return 1;
        if (options.dumpJsonFile && !options.loadIRFromJson)
            JSONGenerator(*openFile(options.dumpJsonFile, true), true) << program << std::endl;
    } catch (const std::exception &bug) {
        std::cerr << bug.what() << std::endl;
        return 1;
    }
    if (::errorCount() > 0)
        return 1;

    auto backend = new BMV2::SimpleSwitchBackend(options, &midEnd.refMap,
                                                 &midEnd.typeMap, &midEnd.enumMap);

    // Necessary because BMV2Context is expected at the top of stack in further processing
    AutoCompileContext autoContext(new BMV2::BMV2Context(BMV2::SimpleSwitchContext::get()));
    try {
        backend->convert(toplevel);
    } catch (const std::exception &bug) {
        std::cerr << bug.what() << std::endl;
        return 1;
    }
    if (::errorCount() > 0)
        return 1;

    if (!options.outputFile.isNullOrEmpty()) {
        std::ostream* out = openFile(options.outputFile, false);
        if (out != nullptr) {
            backend->serialize(*out);
            out->flush();
        }
    }
    return ::errorCount() > 0;
}
