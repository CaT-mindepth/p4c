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

#include "gtest/gtest.h"

#include "frontends/common/options.h"
#include "helpers.h"
#include "lib/log.h"

extern const char* pkt_field_table_info;
extern const char* file_for_dep_info;

const char* pkt_field_table_info;
const char* file_for_dep_info;

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    AutoCompileContext autoGTestContext(new GTestContext);

    GTestContext::get().options().process(argc, argv);
    if (diagnosticCount() > 0) return -1;

    // Initialize the global test environment.
    (void) P4CTestEnvironment::get();

    return RUN_ALL_TESTS();
}
